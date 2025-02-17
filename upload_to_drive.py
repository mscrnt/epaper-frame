#!/usr/bin/env python3
import sys
import os
import io
import logging
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from dotenv import load_dotenv  # ✅ Load from .env and .secrets

# ✅ Load environment variables from .env and .secrets
load_dotenv()  # Load from .env
if os.path.exists(".secrets"):
    load_dotenv(".secrets")  # Load from .secrets

# Configure logging
logging.basicConfig(level=logging.INFO)

LOG_FILE_NAME = "epaper_logs.txt"  # Main log file
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB

def authenticate_drive(service_account_file):
    """Authenticate Google Drive API."""
    try:
        creds = service_account.Credentials.from_service_account_file(service_account_file)
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        logging.error(f"❌ Google Drive authentication failed: {e}")
        sys.exit(1)

def upload_file(drive_service, file_path, folder_id):
    """Upload a file to Google Drive."""
    file_metadata = {
        "name": os.path.basename(file_path),
        "parents": [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype="text/plain")

    try:
        file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        logging.info(f"✅ Uploaded log file to Google Drive (File ID: {file['id']})")
    except Exception as e:
        logging.error(f"❌ Failed to upload log file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("❌ No file specified for upload.")
        sys.exit(1)

    local_log_path = sys.argv[1]

    # ✅ Load Google Drive credentials directly from environment variables
    DRIVE_LOGS_FOLDER_ID = os.getenv("GOOGLE_DRIVE_LOG_FOLDER_ID")
    SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT")

    if not DRIVE_LOGS_FOLDER_ID:
        logging.error("❌ GOOGLE_DRIVE_LOG_FOLDER_ID is not set.")
        sys.exit(1)

    if not SERVICE_ACCOUNT_FILE:
        logging.error("❌ GOOGLE_SERVICE_ACCOUNT is not set.")
        sys.exit(1)

    drive_service = authenticate_drive(SERVICE_ACCOUNT_FILE)

    # Upload the log file
    upload_file(drive_service, local_log_path, DRIVE_LOGS_FOLDER_ID)
