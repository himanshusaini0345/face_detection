from dataclasses import dataclass

@dataclass
class ExtractedFace:
    face_id: str
    photo_id: str
    saved_path: str
    confidence: float
