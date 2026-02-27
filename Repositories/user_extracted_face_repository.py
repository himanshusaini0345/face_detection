import os


class UserExtractedFaceRepository:

    def __init__(self, connection):
        self.conn = connection

    def insert_matches(self, extracted_face_id, matches):
        cursor = self.conn.cursor()

        for match in matches:
            employee_id = os.path.splitext(os.path.basename(match["identity"]))[0]

            cursor.execute(
                """
                INSERT INTO images.user_extracted_faces
                (extracted_face_id, employee_id, distance)
                VALUES (?, ?, ?)
            """,
                extracted_face_id,
                employee_id,
                match["distance"],
            )

        self.conn.commit()
