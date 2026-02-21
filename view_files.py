from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

# Path to the JSON key you downloaded
SERVICE_ACCOUNT_FILE = "drive-image-access-488104-dfeb01003fac.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

# This is the secret sauce:
# 'subject' tells the robot "Pretend to be THIS person"
delegated_credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES, subject="ai@subharti.org"
)

service = build("drive", "v3", credentials=delegated_credentials)

# Now you can list files for that specific user
results = service.files().list(pageSize=10).execute()
files = results.get("files", [])
print(json.dumps(files, indent=4))
