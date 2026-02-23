import pymssql


class EmployeeRepository:
    def __init__(self, host: str, user: str, password: str, database: str):
        self._host     = host
        self._user     = user
        self._password = password
        self._database = database

    def get_face_photo_path(self, employee_id: str) -> str | None:
        conn = pymssql.connect(
            server=self._host,
            user=self._user,
            password=self._password,
            database=self._database,
        )
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT FacePhoto FROM emp.employees WHERE Id = %s",
                (employee_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()