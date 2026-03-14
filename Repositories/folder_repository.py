class FolderRepository:

    def __init__(self, connection):
        self.conn = connection

    def insert(self, folder_ids: list[str]):
        cursor = self.conn.cursor()

        cursor.executemany(
            """
            INSERT INTO images.folders (folder_id)
            SELECT ?
            WHERE NOT EXISTS (
                SELECT 1 FROM images.folders WHERE folder_id = ?
            )
            """,
            [(fid, fid) for fid in folder_ids],
        )

        self.conn.commit()

    def get_folders_for_detection(self) -> list[str]:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT folder_id
            FROM images.folders
            WHERE face_detected = 0
            """
        )

        return [row[0] for row in cursor.fetchall()]

    def mark_face_detected(self, folder_id: str):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE images.folders
            SET
                face_detected = 1,
                last_face_detected = GETDATE()
            WHERE folder_id = ?
            """,
            folder_id,
        )

        self.conn.commit()

    def get_folders_for_recognition(self) -> list[str]:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT folder_id
            FROM images.folders
            WHERE face_detected = 1
            AND face_recognized = 0
            """
        )

        return [row[0] for row in cursor.fetchall()]
    
    def mark_face_recognized(self, folder_id: str):
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE images.folders
            SET
                face_recognized = 1,
                last_face_recognized = GETDATE()
            WHERE folder_id = ?
            """,
            folder_id,
        )

        self.conn.commit()

    def get_unprocessed_folders(self) -> list[str]:
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT folder_id
            FROM images.folders
            WHERE face_detected = 0
            AND face_recognized = 0
            """
        )

        return [row[0] for row in cursor.fetchall()]