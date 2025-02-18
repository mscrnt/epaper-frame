import os
import random
import io
import logging
import socket
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import google.auth.transport.requests
import googleapiclient.discovery
from config import CONFIG  # Import entire config dictionary

# Configure logging
logging.basicConfig(level=logging.INFO)

# Allowed image formats
VALID_EXTENSIONS = ('.bmp', '.png', '.jpg', '.jpeg', '.jfif', '.webp')

def is_internet_available():
    """Check if internet is available by pinging a reliable server."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

def authenticate_drive():
    """Authenticate and return Google Drive service without using deprecated file_cache."""
    if not is_internet_available():
        logging.warning("⚠ No internet connection. Falling back to local images.")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(CONFIG["SERVICE_ACCOUNT_FILE"])
        return googleapiclient.discovery.build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        logging.error(f"❌ Google Drive authentication failed: {e}")
        return None

def get_drive_image_files():
    """Fetch available image files from Google Drive."""
    drive_service = authenticate_drive()
    if not drive_service:
        return []

    try:
        results = drive_service.files().list(
            q=f"'{CONFIG['DRIVE_FOLDER_ID']}' in parents and (mimeType contains 'image/')",
            fields="files(id, name)"
        ).execute()
        files = results.get("files", [])
        if not files:
            logging.warning("⚠ No images found in Google Drive.")
        return files
    except Exception as e:
        logging.error(f"❌ Error retrieving images from Google Drive: {e}")
        return []

def fetch_drive_image(file_id):
    """Stream image from Google Drive."""
    drive_service = authenticate_drive()
    if not drive_service:
        return None

    try:
        request = drive_service.files().get_media(fileId=file_id)
        img_data = io.BytesIO()
        downloader = MediaIoBaseDownload(img_data, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()

        img_data.seek(0)
        return img_data
    except Exception as e:
        logging.error(f"❌ Error downloading image from Google Drive: {e}")
        return None

def get_local_image_files():
    """Fetch available image files from local storage."""
    try:
        return [
            os.path.join(CONFIG["LOCAL_IMAGE_DIR"], f)
            for f in os.listdir(CONFIG["LOCAL_IMAGE_DIR"])
            if f.lower().endswith(VALID_EXTENSIONS)
        ]
    except Exception as e:
        logging.error(f"❌ Error accessing local images: {e}")
        return []

def get_random_image():
    """Fetch a random image from Google Drive or local storage."""
    if CONFIG["IMAGE_SOURCE"] == "drive":
        images = get_drive_image_files()
        if images:
            selected = random.choice(images)
            logging.info(f"📂 Selected Drive image: {selected['name']}")
            return fetch_drive_image(selected["id"])

        logging.warning("⚠ No images found in Google Drive or internet unavailable. Switching to local storage.")

    # Fallback to local storage
    images = get_local_image_files()
    if images:
        selected = random.choice(images)
        logging.info(f"🖼 Selected Local image: {selected}")
        return selected  # File path

    logging.error("❌ No images found in both Google Drive and local storage.")
    return None
