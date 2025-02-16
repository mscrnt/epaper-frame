import os
import random
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from config import CONFIG  # Import entire config dictionary

# Allowed image formats
VALID_EXTENSIONS = ('.bmp', '.png', '.jpg', '.jpeg', '.jfif', '.webp')

def authenticate_drive():
    """Authenticate and return Google Drive service."""
    creds = service_account.Credentials.from_service_account_file(CONFIG["SERVICE_ACCOUNT_FILE"])
    return build("drive", "v3", credentials=creds)

def get_drive_image_files():
    """Fetch available image files from Google Drive."""
    drive_service = authenticate_drive()
    results = drive_service.files().list(
        q=f"'{CONFIG['DRIVE_FOLDER_ID']}' in parents and (mimeType contains 'image/')",
        fields="files(id, name)"
    ).execute()
    
    return results.get("files", [])

def fetch_drive_image(file_id):
    """Stream image from Google Drive."""
    drive_service = authenticate_drive()
    request = drive_service.files().get_media(fileId=file_id)
    img_data = io.BytesIO()
    downloader = MediaIoBaseDownload(img_data, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    img_data.seek(0)
    return img_data

def get_local_image_files():
    """Fetch available image files from local storage."""
    return [
        os.path.join(CONFIG["LOCAL_IMAGE_DIR"], f)
        for f in os.listdir(CONFIG["LOCAL_IMAGE_DIR"])
        if f.lower().endswith(VALID_EXTENSIONS)
    ]

def get_random_image():
    """Fetch a random image from the selected source."""
    if CONFIG["IMAGE_SOURCE"] == "drive":
        images = get_drive_image_files()
        if not images:
            print("No images found in Google Drive.")
            return None
        selected = random.choice(images)
        print("Selected Drive image:", selected["name"])
        return fetch_drive_image(selected["id"])
    
    # Local storage
    images = get_local_image_files()
    if not images:
        print("No images found in local directory.")
        return None
    selected = random.choice(images)
    print("Selected Local image:", selected)
    return selected  # File path
