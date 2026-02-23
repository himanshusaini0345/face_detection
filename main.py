import psycopg2
from googleapiclient.discovery import build
from google.oauth2 import service_account
from fastapi import FastAPI

from config import Config
from utils.face_detection_util import FaceDetector
from utils.embedding_util import EmbeddingGenerator
from utils.http_client import HttpClient
from repository.photo_repository import PhotoRepository
from repository.employee_repository import EmployeeRepository
from service.drive_service import DriveService
from service.face_service import FaceService
from service.photo_service import PhotoService
from controller.photo_controller import router
from jobs.drive_index_job import start_index_job


def build_drive_client(cfg):
    creds = service_account.Credentials.from_service_account_file(
        cfg.SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive"],
        subject=cfg.DRIVE_SUBJECT,
    )
    return build("drive", "v3", credentials=creds)


def create_app() -> FastAPI:
    app = FastAPI()
    cfg = Config()

    pg_conn = psycopg2.connect(cfg.PG_URI)
    drive_client = build_drive_client(cfg)

    photo_repo = PhotoRepository(pg_conn)
    employee_repo = EmployeeRepository(
        host=cfg.MSSQL_HOST,
        user=cfg.MSSQL_USER,
        password=cfg.MSSQL_PASSWORD,
        database=cfg.MSSQL_DB,
    )

    http_client = HttpClient(cfg.EMS_BASE_URL)
    face_det = FaceDetector()  # shared instance — loads model once
    emb_gen = EmbeddingGenerator()

    drive_svc = DriveService(drive_client)
    face_svc = FaceService(employee_repo, http_client, face_det)  # ✅ pass face_det
    photo_svc = PhotoService(
        drive_service=drive_svc,
        repo=photo_repo,
        face_detector=face_det,
        embedding_generator=emb_gen,
        http_client=http_client,
        face_service=face_svc,
    )

    app.include_router(router(photo_svc))
    # start_index_job(photo_svc, cfg.INDEX_INTERVAL_HOURS)

    return app


app = create_app()
