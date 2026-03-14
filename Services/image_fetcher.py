from Models.photo import Photo
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

    def get_images_from_folder(self, folder_id: str, limit: int = 1000) -> list[Photo]:
        """
            Gets Images from google drive for a given folder.
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

            # 2️⃣ Fetch image files inside folder
            results = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false",
                    fields="files(id,webViewLink)",
                    pageSize=limit,
                )
                .execute()
            )

            files = results.get("files", [])

            photos: list[Photo] = []
            for file in files:
                photos.append(
                    Photo(
                        id=file.get("id"),
                        folder_id=folder_id,
                        webview_link=file.get("webViewLink"),
                    )
                )

            return photos

        except (HttpError, google.auth.exceptions.GoogleAuthError, Exception):
            # Network issue, permission issue, invalid folder, etc.
            return []

    def count_images_in_folder(self, folder_id: str) -> int:
        """
            Returns number of image files inside a folder.
            Returns 0 if folder invalid or error occurs.
        """

        if not self.service:
            return 0

        try:
            # Validate folder
            folder = (
                self.service.files()
                .get(fileId=folder_id, fields="id,mimeType")
                .execute()
            )

            if folder.get("mimeType") != "application/vnd.google-apps.folder":
                return 0

            # Count only image files
            results = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false",
                    fields="files(id)",
                    pageSize=1000,
                )
                .execute()
            )

            files = results.get("files", [])
            return len(files)

        except Exception:
            return 0

    def get_folder_by_name(
        self, folder_name: str, parent_folder_id: str = None
    ) -> list[any] | None:
        """
        Returns the folder details for a given folder name.
        Optionally restrict search to a parent folder.
        """
        if not self.service:
            return None

        try:
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"

            results = (
                self.service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="files(id, name)",
                    pageSize=1,
                )
                .execute()
            )

            folders = results.get("files", [])

            if not folders:
                return None

            return folders

        except Exception:
            return None
