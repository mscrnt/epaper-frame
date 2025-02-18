#!/usr/bin/env python3
import os
import sys
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from dotenv import load_dotenv

# ✅ Load environment variables from .env and .secrets
load_dotenv()
if os.path.exists(".secrets"):
    load_dotenv(".secrets")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Google Drive credentials and folder ID
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT")
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
PHOTOS_DIR = "/mnt/photos"

def authenticate_drive():
    """Authenticate Google Drive API."""
    try:
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        logging.error(f"❌ Google Drive authentication failed: {e}")
        sys.exit(1)

def list_drive_files(drive_service, folder_id):
    """List files in the target Google Drive folder to prevent duplicates."""
    query = f"'{folder_id}' in parents and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    return {file["name"]: file["id"] for file in results.get("files", [])}

def upload_file(drive_service, file_path, folder_id):
    """Upload a file to Google Drive."""
    file_name = os.path.basename(file_path)

    file_metadata = {
        "name": file_name,
        "parents": [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype="application/octet-stream", resumable=True)

    try:
        file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        logging.info(f"✅ Uploaded {file_name} (File ID: {file['id']})")
    except Exception as e:
        logging.error(f"❌ Failed to upload {file_name}: {e}")

def upload_all_photos():
    """Uploads all files from /mnt/photos to Google Drive."""
    if not DRIVE_FOLDER_ID:
        logging.error("❌ GOOGLE_DRIVE_FOLDER_ID is not set.")
        sys.exit(1)

    if not SERVICE_ACCOUNT_FILE:
        logging.error("❌ GOOGLE_SERVICE_ACCOUNT is not set.")
        sys.exit(1)

    drive_service = authenticate_drive()
    drive_files = list_drive_files(drive_service, DRIVE_FOLDER_ID)

    # Ensure the directory exists
    if not os.path.exists(PHOTOS_DIR):
        logging.error(f"❌ Directory {PHOTOS_DIR} does not exist.")
        sys.exit(1)

    for file_name in os.listdir(PHOTOS_DIR):
        file_path = os.path.join(PHOTOS_DIR, file_name)

        # Skip directories
        if not os.path.isfile(file_path):
            continue

        # Skip files that already exist in Google Drive
        if file_name in drive_files:
            logging.info(f"⏭️ Skipping {file_name} (Already uploaded)")
            continue

        logging.info(f"📤 Uploading {file_name}...")
        upload_file(drive_service, file_path, DRIVE_FOLDER_ID)

if __name__ == "__main__":
    upload_all_photos()
