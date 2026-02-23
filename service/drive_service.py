# service/drive_service.py


class DriveService:
    def __init__(self, drive_client):
        self.drive = drive_client

    def get_recent_images(self, since_iso_time):
        query = f"mimeType contains 'image/' and createdTime > '{since_iso_time}'"
        results = (
            self.drive.files()
            .list(
                q=query,
                fields="files(id,name,webViewLink,createdTime)",
            )
            .execute()
        )
        return results.get("files", [])

    def download_file(self, file_id):
        request = self.drive.files().get_media(fileId=file_id)
        return request.execute()

    def get_file_metadata(self, file_id: str) -> dict | None:
        """Fetch metadata for a single file by ID. Returns None if not found."""
        try:
            return (
                self.drive.files()
                .get(
                    fileId=file_id,
                    fields="id,name,webViewLink,mimeType",
                )
                .execute()
            )
        except Exception:
            return None
