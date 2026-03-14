import os

from Models.user_photo import UserPhoto


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

    def get_by_user_id(self, user_id) -> list[UserPhoto]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                p.webview_link,
                uef.employee_id
            FROM images.user_extracted_faces uef
            JOIN images.extracted_faces ef
                ON uef.extracted_face_id = CONCAT(ef.photo_id,'_',ef.face_id)
            JOIN images.photos p
                ON ef.photo_id = p.id
            WHERE uef.employee_id = ?
            ORDER BY uef.matched_at DESC
        """,
            user_id,
        )

        columns = [c[0] for c in cursor.description]

        return [UserPhoto(**dict(zip(columns, row))) for row in cursor.fetchall()]
