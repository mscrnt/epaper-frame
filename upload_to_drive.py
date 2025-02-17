#!/usr/bin/env python3
import sys
import os
import io
import logging
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(level=logging.INFO)

LOG_FILE_NAME = "epaper_logs.txt"  # Main log file
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB

# ✅ Filter out unexpected arguments BEFORE importing config.py
VALID_ARGS = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
if len(VALID_ARGS) < 1:
    logging.error("❌ No file specified for upload.")
    sys.exit(1)

# ✅ Now safely import config.py without interfering with argparse
import config
CONFIG = config.get_config()

def authenticate_drive(service_account_file):
    """Authenticate Google Drive API."""
    try:
        creds = service_account.Credentials.from_service_account_file(service_account_file)
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        logging.error(f"❌ Google Drive authentication failed: {e}")
        sys.exit(1)

def upload_file(drive_service, file_path, folder_id, existing_file_id=None):
    """Upload a file to Google Drive (replace if exists)."""
    file_metadata = {
        "name": os.path.basename(file_path),
        "parents": [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype="text/plain")

    try:
        if existing_file_id:
            file = drive_service.files().update(fileId=existing_file_id, media_body=media).execute()
            logging.info(f"✅ Updated existing log file in Google Drive (File ID: {file['id']})")
        else:
            file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            logging.info(f"✅ Uploaded new log file to Google Drive (File ID: {file['id']})")
    except Exception as e:
        logging.error(f"❌ Failed to upload log file: {e}")

if __name__ == "__main__":
    local_log_path = VALID_ARGS[0]

    DRIVE_LOGS_FOLDER_ID = CONFIG.get("GOOGLE_DRIVE_LOG_FOLDER_ID")
    SERVICE_ACCOUNT_FILE = CONFIG.get("SERVICE_ACCOUNT_FILE")

    if not DRIVE_LOGS_FOLDER_ID:
        logging.error("❌ GOOGLE_DRIVE_LOG_FOLDER_ID is not set in config.py.")
        sys.exit(1)

    drive_service = authenticate_drive(SERVICE_ACCOUNT_FILE)

    # Upload the log file
    upload_file(drive_service, local_log_path, DRIVE_LOGS_FOLDER_ID)
