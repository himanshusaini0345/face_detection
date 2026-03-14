from Models.extracted_face import ExtractedFace

class ExtractedFaceRepository:

    def __init__(self, connection):
        self.conn = connection

    def insert(self, face: ExtractedFace):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO images.extracted_faces (face_id, photo_id, confidence)
            SELECT ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM images.extracted_faces
                WHERE photo_id = ? AND face_id = ?
            )
            """,
            face.face_id,
            face.photo_id,
            face.confidence,
            face.photo_id,
            face.face_id,
        )
        self.conn.commit()

    def get_faces_by_photo(self, photo_id: str) -> list[ExtractedFace]:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT face_id, photo_id, confidence
            FROM images.extracted_faces
            WHERE photo_id = ?
            """,
            photo_id,
        )

        rows = cursor.fetchall()

        return [
            ExtractedFace(
                face_id=row[0],
                photo_id=row[1],
                confidence=row[2],
            )
            for row in rows
        ]
