# repository/folder_repository.py


class FolderRepository:
    def __init__(self, conn):
        self.conn = conn

    def upsert_folder(self, folder_id: str, name: str, parent_id: str | None):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO drive_folders (id, name, parent_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE
                SET name = EXCLUDED.name,
                    parent_id = EXCLUDED.parent_id
            """,
            (folder_id, name, parent_id),
        )
        self.conn.commit()

    def upsert_file(
        self, file_id: str, name: str, webviewlink: str, folder_id: str | None
    ):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO drive_files (id, name, webviewlink, folder_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
                SET name        = EXCLUDED.name,
                    webviewlink = EXCLUDED.webviewlink,
                    folder_id   = EXCLUDED.folder_id
            """,
            (file_id, name, webviewlink, folder_id),
        )
        self.conn.commit()

    def get_children(self, folder_id: str | None) -> dict:
        """
        Returns one level of the tree under folder_id.
        folder_id=None means root.
        """
        cur = self.conn.cursor()

        # subfolders
        cur.execute(
            """
            SELECT id, name FROM drive_folders
            WHERE parent_id IS NOT DISTINCT FROM %s
            ORDER BY name
            """,
            (folder_id,),
        )
        folders = [{"id": r[0], "name": r[1], "type": "folder"} for r in cur.fetchall()]

        # files
        cur.execute(
            """
            SELECT id, name, webviewlink FROM drive_files
            WHERE folder_id IS NOT DISTINCT FROM %s
            ORDER BY name
            """,
            (folder_id,),
        )
        files = [
            {"id": r[0], "name": r[1], "webViewLink": r[2], "type": "file"}
            for r in cur.fetchall()
        ]

        return {"folders": folders, "files": files}

    def get_folder_name(self, folder_id: str) -> str | None:
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM drive_folders WHERE id = %s", (folder_id,))
        row = cur.fetchone()
        return row[0] if row else None

    def get_matched_folders_and_files(self, webviewlinks: list[str]) -> dict:
        """
        Given matched webviewlinks from face search, return the
        folder+file structure containing those files — grouped by folder.
        Used to show WHERE the matched photos live in the Drive tree.
        """
        if not webviewlinks:
            return {"folders": [], "files": []}

        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT f.id, f.name, f.webviewlink, f.folder_id,
                   fld.name as folder_name
            FROM drive_files f
            LEFT JOIN drive_folders fld ON fld.id = f.folder_id
            WHERE f.webviewlink = ANY(%s)
            ORDER BY fld.name, f.name
            """,
            (webviewlinks,),
        )
        rows = cur.fetchall()

        folders_seen = {}
        files = []
        for file_id, name, webviewlink, folder_id, folder_name in rows:
            files.append(
                {
                    "id": file_id,
                    "name": name,
                    "webViewLink": webviewlink,
                    "folder_id": folder_id,
                    "type": "file",
                }
            )
            if folder_id and folder_id not in folders_seen:
                folders_seen[folder_id] = {
                    "id": folder_id,
                    "name": folder_name,
                    "type": "folder",
                }

        return {
            "folders": list(folders_seen.values()),
            "files": files,
        }
