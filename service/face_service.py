from IPython.display import Image


class FaceService:
    """
    Resolves a user ID → image using:
      1. EmployeeRepository  (SQL Server) → FacePhoto path
      2. HttpClient          (HTTP)       → PIL Image
    """

    def __init__(self, employee_repo, http_client):
        self.employee_repo = employee_repo
        self.http_client = http_client

    def get_user_image(self, employee_id: str) -> Image:
        path = self.employee_repo.get_face_photo_path(employee_id)
        print(f"[FaceService] got path from repo: {path}")
        if not path:
            raise ValueError(f"No face photo found for employee {employee_id}")
        return self.http_client.fetch_image_from_path(path)
