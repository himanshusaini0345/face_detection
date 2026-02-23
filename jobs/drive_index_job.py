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

        for folder in folders:
            self.folder_repo.upsert_folder(
                folder_id=folder["id"],
                name=folder["name"],
                parent_id=None,
            )

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
        if since_iso:
            images = self.drive_service.get_recent_images(since_iso)
            print(f"[index] fetching images since {since_iso}")
        else:
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
                if not page_token or len(images) >= 10000:  # safety
                    break
            print(f"[index] total: {len(images)} image files")

        # ── resume: load already-processed file IDs ───────────
        conn = self.photo_repo.conn
        cur = conn.cursor()
        cur.execute("SELECT file_id FROM indexed_files")
        already_done = {row[0] for row in cur.fetchall()}
        pending = [img for img in images if img["id"] not in already_done]
        print(
            f"[resume] total={len(images)}  already_done={len(already_done)}  pending={len(pending)}"
        )

        success, skipped, errors = 0, 0, 0

        for i, img_meta in enumerate(pending):
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
                    # mark skipped so we don't retry unreadable files forever
                    cur.execute(
                        "INSERT INTO indexed_files (file_id) VALUES (%s) ON CONFLICT DO NOTHING",
                        (img_meta["id"],),
                    )
                    conn.commit()
                    continue

                faces = self.face_detector.extract_faces(cv_img)
                if not faces:
                    skipped += 1
                    cur.execute(
                        "INSERT INTO indexed_files (file_id) VALUES (%s) ON CONFLICT DO NOTHING",
                        (img_meta["id"],),
                    )
                    conn.commit()
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

                # checkpoint — mark as done after successful embed
                cur.execute(
                    "INSERT INTO indexed_files (file_id) VALUES (%s) ON CONFLICT DO NOTHING",
                    (img_meta["id"],),
                )
                conn.commit()

                success += 1
                print(
                    f"[{i+1}/{len(pending)}] indexed {len(faces)} face(s): {img_meta['name']}"
                )

            except Exception as e:
                # do NOT checkpoint on error — will retry next run
                errors += 1
                print(f"[{i+1}/{len(pending)}] ERROR {img_meta.get('name')}: {e}")

        print(f"\ndone. indexed={success}  skipped={skipped}  errors={errors}")

    def run_incremental(self):
        since = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
        self.sync_folders()
        self.sync_files_and_index_faces(since_iso=since)

    def run_full(self):
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
