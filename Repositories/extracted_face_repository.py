class ExtractedFaceRepository:

    def __init__(self, connection):
        self.conn = connection

    def insert(self, face):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO images.extracted_faces (id, photo_id, local_path, confidence)
            VALUES (?, ?, ?, ?)
        """,
            face.face_id,
            face.photo_id,
            face.saved_path,
            face.confidence,
        )
        self.conn.commit()
