from Models.photo import Photo


class PhotoRepository:

    def __init__(self, connection):
        self.conn = connection

    def insert_photo(self, photo: Photo):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            IF NOT EXISTS (SELECT 1 FROM images.photos WHERE id=?)
            INSERT INTO images.photos (id, folder_name, webview_link, processed)
            VALUES (?, ?, ?, 0)
        """,
            photo.photo_id,
            photo.photo_id,
            photo.folder_name,
            photo.photo_link,
        )
        self.conn.commit()

    def mark_processed(self, photo_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE images.photos SET processed=1 WHERE id=?
        """,
            photo_id,
        )
        self.conn.commit()

    def is_processed(self, photo_id):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT processed 
            FROM images.photos 
            WHERE id = ?
            """,
            photo_id,
        )

        row = cursor.fetchone()

        if row is None:
            return False   # photo not found (safe fallback)

        return bool(row[0])
