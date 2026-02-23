import numpy as np
import cv2
from PIL import Image
from datetime import datetime, timedelta


def _crop_all_faces(cv_img, faces):
    """Return a list of PIL RGB images, one per detected face."""
    crops = []
    for x, y, w, h in faces:
        crop = cv_img[y : y + h, x : x + w]
        crops.append(Image.fromarray(crop).convert("RGB"))
    return crops


def _bytes_to_grayscale(file_bytes: bytes):
    """
    Saves bytes to a temp file and reads with cv2.imread(..., 0)
    — exactly what the original script does.
    """
    import tempfile, os

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        cv_img = cv2.imread(tmp_path, 0)  # 0 = grayscale, same as original
    finally:
        os.remove(tmp_path)  # always clean up

    return cv_img  # None if imread failed


class PhotoService:

    def __init__(
        self,
        drive_service,
        repo,
        face_detector,
        embedding_generator,
        http_client,
        face_service,
    ):
        self.drive_service = drive_service
        self.repo = repo
        self.face_detector = face_detector
        self.embedding_generator = embedding_generator
        self.http_client = http_client
        self.face_service = face_service

    # ----------------------------------------------------------
    # Background job
    # ----------------------------------------------------------
    def index_last_24_hours(self):
        since = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
        images = self.drive_service.get_recent_images(since)

        for img_meta in images:
            try:
                file_bytes = self.drive_service.download_file(img_meta["id"])

                cv_img = _bytes_to_grayscale(file_bytes)  # fixed decode
                if cv_img is None:
                    continue

                faces = self.face_detector.extract_faces(cv_img)
                if len(faces) == 0:
                    continue

                for face_pil in _crop_all_faces(cv_img, faces):
                    embedding = self.embedding_generator.generate(face_pil)
                    self.repo.save_embedding(
                        file_id=img_meta["id"],
                        webviewlink=img_meta["webViewLink"],
                        embedding=embedding,
                    )

            except Exception as e:
                print(f"[index_job] skipping {img_meta.get('id')}: {e}")

    # ----------------------------------------------------------
    # API handler
    # ----------------------------------------------------------
    def find_user_photos(self, employee_id: str) -> list[str]:
        user_image = self.face_service.get_user_image(employee_id)
        user_image.show(title=f"employee_{employee_id}")  # DEBUG
        embedding = self.embedding_generator.generate(user_image)
        return self.repo.find_similar(embedding)

    # ----------------------------------------------------------
    # Manual single-file indexing
    # ----------------------------------------------------------
    def index_single_file(self, file_id: str) -> dict:
        # 1. metadata
        meta = self.drive_service.get_file_metadata(file_id)
        if not meta:
            return {"status": "error", "reason": "file not found in Drive"}

        # 2. download
        file_bytes = self.drive_service.download_file(file_id)

        # 3. decode — fixed: color first, then grayscale
        cv_img = _bytes_to_grayscale(file_bytes)
        if cv_img is None:
            return {"status": "error", "reason": "could not decode image"}

        # DEBUG — show the full image before face detection
        Image.fromarray(cv_img).show(title=f"{file_id}_full")

        # 4. detect
        faces = self.face_detector.extract_faces(cv_img)
        if len(faces) == 0:
            return {"status": "skipped", "reason": "no face detected in image"}

        # 5. embed ALL faces and save each one
        for i, face_pil in enumerate(_crop_all_faces(cv_img, faces)):
            face_pil.show(title=f"{file_id}_face_{i}")  # DEBUG
            embedding = self.embedding_generator.generate(face_pil)
            self.repo.save_embedding(
                file_id=file_id,
                webviewlink=meta["webViewLink"],
                embedding=embedding,
            )

        return {
            "status": "indexed",
            "file_id": file_id,
            "webViewLink": meta["webViewLink"],
            "file_name": meta.get("name"),
            "faces_indexed": len(faces),
        }
