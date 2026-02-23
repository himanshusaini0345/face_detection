# service/face_service.py

import cv2
import numpy as np
from PIL import Image
import io


class FaceService:
    """
    Resolves employee ID → cropped face PIL image:
      1. EmployeeRepository (SQL Server) → FacePhoto path
      2. HttpClient         (HTTP)       → raw image bytes
      3. FaceDetector                    → crop best face
    """

    def __init__(self, employee_repo, http_client, face_detector):
        self.employee_repo = employee_repo
        self.http_client = http_client
        self.face_detector = face_detector

    def get_user_image(self, employee_id: str) -> Image.Image:
        # 1. get path from SQL Server
        path = self.employee_repo.get_face_photo_path(employee_id)
        if not path:
            raise ValueError(f"No face photo found for employee {employee_id}")

        # 2. fetch image over HTTP
        pil_img = self.http_client.fetch_image_from_path(path)
        pil_img.show(title=f"employee_{employee_id}_raw")  # DEBUG

        # 3. detect + crop best face (same pipeline as indexing)
        img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        cropped = self.face_detector.extract_best_face(img_bgr)

        if cropped is None:
            print(
                f"[face_service] no face detected for {employee_id} — using full image"
            )
            return pil_img

        face_pil = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
        face_pil.show(title=f"employee_{employee_id}_crop")  # DEBUG
        return face_pil
