import os
import pyodbc
from dotenv import load_dotenv


def get_connection():
    """
    Returns a pyodbc connection.
    Returns None if connection fails.
    """

    try:
        load_dotenv()

        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_NAME")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        port = os.getenv("DB_PORT", "1433")

        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={server},{port};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
        )

        return pyodbc.connect(conn_str)

    except Exception as e:
        print("Database connection error:", e)
        return None
