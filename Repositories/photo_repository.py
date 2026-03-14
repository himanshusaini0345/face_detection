from Models.photo import Photo


class PhotoRepository:

    def __init__(self, connection):
        self.conn = connection

    def insert_photo(self, photo: Photo):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            IF NOT EXISTS (SELECT 1 FROM images.photos WHERE id=?)
            INSERT INTO images.photos (id, folder_id, webview_link)
            VALUES (?, ?, ?)
        """,
            photo.id,
            photo.id,
            photo.folder_id,
            photo.webview_link,
        )

        self.conn.commit()

    def is_detection_done(self, photo_id):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT face_detected
            FROM images.photos
            WHERE id = ?
            """,
            photo_id,
        )

        row = cursor.fetchone()

        return row and bool(row[0])
    
    def is_recognition_done(self, photo_id):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT face_recognized
            FROM images.photos
            WHERE id = ?
            """,
            photo_id,
        )

        row = cursor.fetchone()

        return row and bool(row[0])
    
    def mark_detection_done(self, photo_id):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE images.photos
            SET face_detected = 1,
                last_face_detected = GETDATE()
            WHERE id = ?
            """,
            photo_id,
        )

        self.conn.commit()

    def mark_recognition_done(self, photo_id):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE images.photos
            SET face_recognized = 1,
                last_face_recognized = GETDATE()
            WHERE id = ?
            """,
            photo_id,
        )

        self.conn.commit()