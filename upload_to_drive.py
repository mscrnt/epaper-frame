#!/usr/bin/env python3
import sys
import os
import io
import logging
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from config import CONFIG  # ✅ Load config

# Configure logging
logging.basicConfig(level=logging.INFO)

# Google Drive Folder ID for logs (now read from .secrets via config.py)
DRIVE_LOGS_FOLDER_ID = CONFIG.get("GOOGLE_DRIVE_LOG_FOLDER_ID")
LOG_FILE_NAME = "epaper_logs.txt"  # Main log file
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB

def authenticate_drive():
    """Authenticate Google Drive API."""
    try:
        creds = service_account.Credentials.from_service_account_file(CONFIG["SERVICE_ACCOUNT_FILE"])
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        logging.error(f"❌ Google Drive authentication failed: {e}")
        sys.exit(1)

def find_existing_log(drive_service):
    """Search for an existing log file in Google Drive."""
    query = f"name='{LOG_FILE_NAME}' and '{DRIVE_LOGS_FOLDER_ID}' in parents and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name, size)").execute()
    files = results.get("files", [])
    return files[0] if files else None  # Return file info if found

def download_existing_log(drive_service, file_id):
    """Download existing log file from Google Drive."""
    request = drive_service.files().get_media(fileId=file_id)
    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_stream.seek(0)
    return file_stream.read().decode("utf-8")  # Convert bytes to string

def upload_file(drive_service, file_path, folder_id, existing_file_id=None):
    """Upload a file to Google Drive (replace if exists)."""
    file_metadata = {
        "name": os.path.basename(file_path),
        "parents": [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype="text/plain")

    try:
        if existing_file_id:
            # Update the existing file instead of creating a new one
            file = drive_service.files().update(fileId=existing_file_id, media_body=media).execute()
            logging.info(f"✅ Updated existing log file in Google Drive (File ID: {file['id']})")
        else:
            # Create a new file if it doesn't exist
            file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            logging.info(f"✅ Uploaded new log file to Google Drive (File ID: {file['id']})")
    except Exception as e:
        logging.error(f"❌ Failed to upload log file: {e}")

def manage_log_file(local_log_path):
    """Check if the log file is too large and rotate if needed."""
    if os.path.exists(local_log_path) and os.path.getsize(local_log_path) > MAX_LOG_SIZE:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        new_log_name = f"epaper_logs_{timestamp}.txt"
        new_log_path = os.path.join(os.path.dirname(local_log_path), new_log_name)

        logging.info(f"📂 Log file exceeded {MAX_LOG_SIZE} bytes, rotating to {new_log_name}")
        os.rename(local_log_path, new_log_path)

        return new_log_path  # Return the rotated log file path
    return local_log_path  # Return original if no rotation is needed

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("❌ No file specified for upload.")
        sys.exit(1)

    local_log_path = sys.argv[1]

    if not DRIVE_LOGS_FOLDER_ID:
        logging.error("❌ GOOGLE_DRIVE_LOG_FOLDER_ID is not set in config.py.")
        sys.exit(1)

    drive_service = authenticate_drive()
    existing_log = find_existing_log(drive_service)

    # Handle log rotation if necessary
    log_file_to_upload = manage_log_file(local_log_path)

    if existing_log:
        logging.info("📥 Existing log file found. Downloading...")
        existing_log_content = download_existing_log(drive_service, existing_log["id"])

        # Append new log data to the existing log
        with open(local_log_path, "r") as new_log_file:
            new_log_content = new_log_file.read()

        merged_log_content = existing_log_content + "\n" + new_log_content

        # Save merged logs back to the local file before upload
        with open(local_log_path, "w") as merged_log_file:
            merged_log_file.write(merged_log_content)

    # Upload (or rotate) the log file
    upload_file(drive_service, log_file_to_upload, DRIVE_LOGS_FOLDER_ID, existing_log["id"] if existing_log else None)
