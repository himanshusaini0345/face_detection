import os
from deepface import DeepFace


class FaceMatcher:
    def __init__(
        self,
        db_path="user_images",
        model_name="Facenet512",
        detector_backend="retinaface",
        distance_metric="cosine",
        threshold=0.3,
    ):
        self.db_path = db_path
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.distance_metric = distance_metric
        self.threshold = threshold

    def match(self, extracted_photo_path: str) -> str:
        """
        Returns:
            - Path of matched image from user_images
            - "" (empty string) if no match
        """

        try:
            results = DeepFace.find(
                img_path=extracted_photo_path,
                db_path=self.db_path,
                detector_backend=self.detector_backend,
                model_name=self.model_name,
                distance_metric=self.distance_metric,
                threshold=self.threshold,
                enforce_detection=False,
            )

            # DeepFace returns list of DataFrames (even for single image)
            if not results or results[0].empty:
                return ""

            best_match = results[0].iloc[0]
            return best_match["identity"]

        except Exception:
            return ""
