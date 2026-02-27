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

    def get_images_from_folder(self, folder_id: str, limit=None):

        files = []
        page_token = None

        while True:
            response = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false",
                    fields="nextPageToken, files(id,name,webViewLink)",
                    pageSize=1000,
                    pageToken=page_token,
                )
                .execute()
            )

            batch = response.get("files", [])
            files.extend(batch)

            if limit and len(files) >= limit:
                return files[:limit]

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return files