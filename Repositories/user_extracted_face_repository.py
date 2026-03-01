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

    def get_by_user_id(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                uef.employee_id,
                ef.local_path,
                p.webview_link,
                uef.distance,
                uef.matched_at
            FROM images.user_extracted_faces uef
            JOIN images.extracted_faces ef
                ON uef.extracted_face_id = ef.id
            JOIN images.photos p
                ON ef.photo_id = p.id
            WHERE uef.employee_id = ?
            ORDER BY uef.matched_at DESC
        """,
            user_id,
        )

        return cursor.fetchall()

    def get_all(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                uef.employee_id,
                ef.local_path,
                p.webview_link,
                uef.distance,
                uef.matched_at
            FROM images.user_extracted_faces uef
            JOIN images.extracted_faces ef
                ON uef.extracted_face_id = ef.id
            JOIN images.photos p
                ON ef.photo_id = p.id
            ORDER BY uef.employee_id, uef.matched_at DESC
        """
        )

        return cursor.fetchall()
