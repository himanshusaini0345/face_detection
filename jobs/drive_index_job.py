# jobs/drive_index_job.py

from datetime import datetime, timedelta
import cv2
import numpy as np
import tempfile
import os
from PIL import Image


class DriveIndexJob:
    def __init__(
        self,
        drive_service,
        photo_service,
        folder_repo,
        face_detector,
        embedding_gen,
        photo_repo,
    ):
        self.drive_service = drive_service
        self.photo_service = photo_service
        self.folder_repo = folder_repo
        self.face_detector = face_detector
        self.embedding_gen = embedding_gen
        self.photo_repo = photo_repo

    def sync_folders(self):
        folders = self.drive_service.get_all_folders()

        # Pass 1 — insert all folders with parent_id=NULL to avoid FK violations
        # (Drive returns folders in arbitrary order so parents may not exist yet)
        for folder in folders:
            self.folder_repo.upsert_folder(
                folder_id=folder["id"],
                name=folder["name"],
                parent_id=None,
            )

        # Pass 2 — all folders now exist, safe to set parent_ids
        for folder in folders:
            parent_id = folder.get("parents", [None])[0]
            if parent_id:
                self.folder_repo.upsert_folder(
                    folder_id=folder["id"],
                    name=folder["name"],
                    parent_id=parent_id,
                )

        print(f"[sync_folders] synced {len(folders)} folders")

    def sync_files_and_index_faces(self, since_iso: str | None = None):
        """
        since_iso: ISO timestamp string e.g. "2024-01-01T00:00:00Z"
                   None = fetch ALL files (no time filter)
        """
        if since_iso:
            # incremental — only new files
            images = self.drive_service.get_recent_images(since_iso)
            print(f"[index] fetching images since {since_iso}")
        else:
            # full — paginate through everything
            images = []
            page_token = None
            while True:
                params = dict(
                    q="mimeType contains 'image/'",
                    fields="nextPageToken, files(id,name,webViewLink,parents)",
                    pageSize=1000,
                )
                if page_token:
                    params["pageToken"] = page_token
                result = self.drive_service.drive.files().list(**params).execute()
                images.extend(result.get("files", []))
                page_token = result.get("nextPageToken")
                print(f"[index] fetched {len(images)} files so far...")
                if not page_token:
                    break
            print(f"[index] total: {len(images)} image files")

        success, skipped, errors = 0, 0, 0

        for i, img_meta in enumerate(images):
            try:
                folder_id = img_meta.get("parents", [None])[0]
                self.folder_repo.upsert_file(
                    file_id=img_meta["id"],
                    name=img_meta["name"],
                    webviewlink=img_meta["webViewLink"],
                    folder_id=folder_id,
                )

                file_bytes = self.drive_service.download_file(img_meta["id"])

                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name
                try:
                    cv_img = cv2.imread(tmp_path)
                finally:
                    os.remove(tmp_path)

                if cv_img is None:
                    skipped += 1
                    continue

                faces = self.face_detector.extract_faces(cv_img)
                if not faces:
                    skipped += 1
                    continue

                for x, y, w, h in faces:
                    crop = cv_img[y : y + h, x : x + w]
                    face_pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                    embedding = self.embedding_gen.generate(face_pil)
                    self.photo_repo.save_embedding(
                        file_id=img_meta["id"],
                        webviewlink=img_meta["webViewLink"],
                        embedding=embedding,
                    )

                success += 1
                print(
                    f"[{i+1}/{len(images)}] indexed {len(faces)} face(s): {img_meta['name']}"
                )

            except Exception as e:
                errors += 1
                print(f"[{i+1}/{len(images)}] ERROR {img_meta.get('name')}: {e}")

        print(f"\ndone. indexed={success}  skipped={skipped}  errors={errors}")

    def run_incremental(self):
        """Called by scheduler every 24h."""
        since = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
        self.sync_folders()
        self.sync_files_and_index_faces(since_iso=since)

    def run_full(self):
        """Called once manually to index everything."""
        self.sync_folders()
        self.sync_files_and_index_faces(since_iso=None)


def start_index_job(job, interval_hours: int = 24):
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        job.run_incremental, "interval", hours=interval_hours, id="drive_index_job"
    )
    scheduler.start()
    return scheduler
