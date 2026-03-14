import os
from Models.extracted_face import ExtractedFace
from Models.photo import Photo
import cv2
import numpy as np
import io
from deepface import DeepFace
from googleapiclient.http import MediaIoBaseDownload


class FaceExtractor:
    def __init__(self, drive_service, output_base="extracted_faces"):
        self.drive_service = drive_service
        self.output_base = output_base
        os.makedirs(self.output_base, exist_ok=True)

    def _download_photo(self, photo_id: str):
        try:
            request = self.drive_service.files().get_media(fileId=photo_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

            file_stream.seek(0)
            file_bytes = np.asarray(bytearray(file_stream.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            print("Download error:", str(e))
            return None

    def extract_from_photo(self, photo: Photo) -> list[ExtractedFace]:
        if not self.drive_service:
            return []

        try:
            image = self._download_photo(photo.id)
            if image is None:
                return None

            photo_folder = os.path.join(self.output_base, photo.id)
            os.makedirs(photo_folder, exist_ok=True)

            face_objs = DeepFace.extract_faces(
                img_path=image,
                detector_backend="retinaface",
                align=True,
                enforce_detection=False,
            )

            extracted_faces = []

            for i, face_obj in enumerate(face_objs):
                face_img = face_obj["face"] * 255
                face_img = face_img.astype("uint8")
                face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)

                filename = f"face_{i}.jpg"
                save_path = os.path.join(photo_folder, filename)
                cv2.imwrite(save_path, face_img)

                extracted_faces.append(
                    ExtractedFace(
                        face_id=f"{photo.id}_{i}",
                        photo_id=photo.id,
                        saved_path=save_path,
                        confidence=float(face_obj.get("confidence", 0.0)),
                    )
                )

            return extracted_faces

        except Exception as e:
            print("Face extraction error:", str(e))
            return None
