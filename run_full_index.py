"""
run_full_index.py — run once to index all existing Drive content.
Usage: python run_full_index.py
"""

import psycopg2
from googleapiclient.discovery import build
from google.oauth2 import service_account

from config import Config
from utils.face_detection_util import FaceDetector
from utils.embedding_util import EmbeddingGenerator
from repository.photo_repository import PhotoRepository
from repository.folder_repository import FolderRepository
from service.drive_service import DriveService
from jobs.drive_index_job import DriveIndexJob

cfg = Config()
pg_conn = psycopg2.connect(cfg.PG_URI)
creds = service_account.Credentials.from_service_account_file(
    cfg.SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/drive"],
    subject=cfg.DRIVE_SUBJECT,
)
drive_client = build("drive", "v3", credentials=creds)

job = DriveIndexJob(
    drive_service=DriveService(drive_client),
    photo_service=None,  # not needed for indexing
    folder_repo=FolderRepository(pg_conn),
    face_detector=FaceDetector(),
    embedding_gen=EmbeddingGenerator(),
    photo_repo=PhotoRepository(pg_conn),
)

job.run_full()
pg_conn.close()
