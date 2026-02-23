import psycopg2
from googleapiclient.discovery import build
from google.oauth2 import service_account
from fastapi import FastAPI

# local imports (shown inline for clarity)
from config import Config
from utils.face_detection_util import FaceDetector
from utils.embedding_util import EmbeddingGenerator
from utils.http_client import HttpClient
from repository.photo_repository import PhotoRepository
from repository.employee_repository import EmployeeRepository
from service.drive_service import DriveService
from service.photo_service import PhotoService
from service.face_service import FaceService
from controller.photo_controller import router
from jobs.drive_index_job import start_index_job

app = FastAPI()


def build_drive_client(config):
    creds = service_account.Credentials.from_service_account_file(
        config.SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive"],
        subject=config.DRIVE_SUBJECT,
    )
    return build("drive", "v3", credentials=creds)


def create_app() -> FastAPI:
    cfg = Config()

    # --- infrastructure ---
    pg_conn = psycopg2.connect(cfg.PG_URI)
    drive_client = build_drive_client(cfg)

    # --- repositories ---
    photo_repo = PhotoRepository(pg_conn)  # Postgres
    employee_repo = EmployeeRepository(      # ✅ pass individual fields
        host=cfg.MSSQL_HOST,
        user=cfg.MSSQL_USER,
        password=cfg.MSSQL_PASSWORD,
        database=cfg.MSSQL_DB,
    )  # SQL Server

    # --- utils ---
    http_client = HttpClient(cfg.EMS_BASE_URL)
    face_det = FaceDetector()
    emb_gen = EmbeddingGenerator()

    # --- services ---
    drive_svc = DriveService(drive_client)      # ✅ wrap the raw client here
    face_svc = FaceService(employee_repo, http_client)
    photo_svc = PhotoService(
        drive_svc, photo_repo, face_det, emb_gen, http_client, face_svc
    )

    # --- controller + job ---
    app.include_router(router(photo_svc))
    # start_index_job(photo_svc, cfg.INDEX_INTERVAL_HOURS)

    return app


# Run once at import so `uvicorn main:app` works
app = create_app()
