import os
import pyodbc
import requests
from dotenv import load_dotenv


class EmployeeImageDownloader:
    def __init__(self):
        load_dotenv()

        self.server = os.getenv("DB_SERVER")
        self.database = os.getenv("DB_NAME")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.port = os.getenv("DB_PORT", "1433")
        self.base_url = os.getenv("BASE_IMAGE_URL")

        self.output_dir = "user_images"
        os.makedirs(self.output_dir, exist_ok=True)

        self.connection = self._connect()

    def _connect(self):
        try:
            conn_str = (
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                "Encrypt=no;"
                "TrustServerCertificate=yes;"
            )
            return pyodbc.connect(conn_str)
        except Exception as e:
            print("DB Connection Error:", e)
            return None

    def download_all_images(self):
        if not self.connection:
            return

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT TOP 100 Id, FacePhoto FROM emp.Employees WHERE Id in(7938,2983,3135,1008)")

            rows = cursor.fetchall()

            for row in rows:
                emp_id = row.Id
                face_photo = row.FacePhoto

                if not face_photo:
                    continue

                full_url = f"{self.base_url}{face_photo}"

                try:
                    response = requests.get(full_url, timeout=10)

                    if response.status_code == 200:
                        file_path = os.path.join(self.output_dir, f"{emp_id}.jpg")

                        with open(file_path, "wb") as f:
                            f.write(response.content)

                        print(f"Downloaded: {file_path}")
                    else:
                        print(f"Failed ({response.status_code}): {full_url}")

                except Exception as e:
                    print(f"Download error for {emp_id}:", e)

        except Exception as e:
            print("Query error:", e)
