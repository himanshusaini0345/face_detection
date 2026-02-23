import os


class Config:
    PG_URI: str = os.getenv(
        "DB_URI", "postgresql://postgres:postgres@127.0.0.1:5432/facedb"
    )
    MSSQL_HOST: str = os.getenv("MSSQL_HOST", "192.168.60.5")
    MSSQL_DB: str = os.getenv("MSSQL_DB", "EMS_WEB_2023")
    MSSQL_USER: str = os.getenv("MSSQL_USER", "erpems")
    MSSQL_PASSWORD: str = os.getenv("MSSQL_PASSWORD", "erpems#@!123")
    
    EMS_BASE_URL: str = os.getenv("EMS_BASE_URL", "https://ems.subharti.org")
    SERVICE_ACCOUNT_FILE: str = os.getenv(
        "SERVICE_ACCOUNT_FILE", "drive-image-access-488104-dfeb01003fac.json"
    )
    DRIVE_SUBJECT: str = os.getenv("DRIVE_SUBJECT", "ai@subharti.org")
    FACE_SIMILARITY_LIMIT: int = int(os.getenv("FACE_SIMILARITY_LIMIT", "20"))
    INDEX_INTERVAL_HOURS: int = int(os.getenv("INDEX_INTERVAL_HOURS", "24"))
