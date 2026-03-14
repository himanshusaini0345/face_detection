from Models.extracted_face import ExtractedFace

class ExtractedFaceRepository:

    def __init__(self, connection):
        self.conn = connection

    def insert(self, face: ExtractedFace):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO images.extracted_faces (face_id, photo_id, confidence)
            VALUES (?, ?, ?, ?)
        """,
            face.face_id,
            face.photo_id,
            face.confidence,
        )
        self.conn.commit()
