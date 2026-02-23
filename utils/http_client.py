import requests
from PIL import Image
import io


class HttpClient:
    def __init__(self, base_url: str):
        """base_url: e.g. 'https://ems.subharti.org'  (no trailing slash)"""
        self.base_url = base_url.rstrip("/")

    def fetch_image_from_path(self, path: str) -> Image.Image:
        """
        Fetches the image at base_url/path.
        path comes from FacePhoto column, e.g. 'uploads/photos/emp_42.jpg'
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")
