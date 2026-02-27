from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.exceptions


class GoogleDriveImageFetcher:
    def __init__(self, service_account_file: str, delegated_user: str):
        self.service_account_file = service_account_file
        self.delegated_user = delegated_user
        self.scopes = ["https://www.googleapis.com/auth/drive"]
        self.service = self._build_service()

    def _build_service(self):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=self.scopes,
                subject=self.delegated_user,
            )
            return build("drive", "v3", credentials=credentials)
        except Exception:
            return None

    def get_images_from_folder(self, folder_id: str):
        """
        Returns:
            [
                {
                    "photo_id": "...",
                    "photo_link": "...",
                    "folder_name": "..."
                }
            ]
        If any error occurs, returns []
        """

        if not self.service:
            return []

        try:
            # 1️⃣ Get folder metadata (to extract folder name)
            folder = (
                self.service.files()
                .get(fileId=folder_id, fields="id,name,mimeType")
                .execute()
            )

            # Validate it's actually a folder
            if folder.get("mimeType") != "application/vnd.google-apps.folder":
                return []

            folder_name = folder.get("name")

            # 2️⃣ Fetch image files inside folder
            results = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false",
                    fields="files(id,name,webViewLink)",
                    pageSize=1000,
                )
                .execute()
            )

            files = results.get("files", [])

            output = []
            for file in files:
                output.append(
                    {
                        "photo_id": file.get("id"),
                        "photo_link": file.get("webViewLink"),
                        "folder_name": folder_name,
                    }
                )

            return output

        except (HttpError, google.auth.exceptions.GoogleAuthError, Exception):
            # Network issue, permission issue, invalid folder, etc.
            return []
