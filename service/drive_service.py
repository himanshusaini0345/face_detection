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
                fields="files(id,name,webViewLink,createdTime,parents)",
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
                    fields="id,name,webViewLink,mimeType,parents",
                )
                .execute()
            )
        except Exception:
            return None

    def get_folder_metadata(self, folder_id: str) -> dict | None:
        try:
            return (
                self.drive.files()
                .get(
                    fileId=folder_id,
                    fields="id,name,parents",
                )
                .execute()
            )
        except Exception:
            return None

    def get_all_folders(self) -> list:
        """Fetch all folders the service account can see, with pagination."""
        folders = []
        page_token = None
        while True:
            params = dict(
                q="mimeType = 'application/vnd.google-apps.folder'",
                fields="nextPageToken, files(id,name,parents)",
                pageSize=1000,
            )
            if page_token:
                params["pageToken"] = page_token
            result = self.drive.files().list(**params).execute()
            folders.extend(result.get("files", []))
            page_token = result.get("nextPageToken")
            if not page_token:
                break
        return folders
