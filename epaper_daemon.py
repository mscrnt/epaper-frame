#!/usr/bin/env python3
import socketserver
import socket
import threading
import importlib
import io
import sys
from PIL import Image, ImageOps
from config import CONFIG
from image_source import get_random_image

# --- Initialize the ePaper Display and SPI Connection ---

print(f"📡 Using real Waveshare ePaper display: {CONFIG['DISPLAY_MODEL']}")
epd_module = importlib.import_module(f"waveshare_epd.{CONFIG['DISPLAY_MODEL']}")
epd = epd_module.EPD()

print("Initializing display and SPI connection...")
if epd.init() != 0:
    print("❌ Failed to initialize display. Exiting.")
    sys.exit(1)
print("Display initialized and SPI connection is open.")

# --- Define 7-color palette for image quantization ---
palette_image = Image.new("P", (1, 1))
palette_image.putpalette((
    0, 0, 0,       # Black
    255, 255, 255, # White
    0, 255, 0,     # Green
    0, 0, 255,     # Blue
    255, 0, 0,     # Red
    255, 255, 0,   # Yellow
    255, 128, 0    # Orange
) + (0, 0, 0) * 249)

# --- Helper Functions ---

def preprocess_image(image_data):
    """Process image for display: resize, rotate if necessary, and quantize."""
    print("🔄 Preprocessing Image...")
    try:
        # Determine if image_data is a file path or an in-memory stream.
        if isinstance(image_data, str):
            print(f"📂 Opening Local Image: {image_data}")
            img = Image.open(image_data)
        elif isinstance(image_data, io.BytesIO):
            print("📡 Opening Image from stream")
            img = Image.open(image_data)
        else:
            raise ValueError("Unsupported image format")
    except Exception as e:
        print(f"❌ Error opening image: {e}")
        return None

    print(f"📏 Original Image Size: {img.size}, Mode: {img.mode}")
    if img.mode in ('RGBA', 'LA'):
        print("🎨 Converting RGBA/LA Image to RGB")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    else:
        img = img.convert("RGB")
    img = ImageOps.exif_transpose(img)
    
    # Calculate scaling and possibly rotate for best fit.
    w, h = img.size
    target_w, target_h = CONFIG["TARGET_SIZE"]
    scale_normal = min(target_w / w, target_h / h)
    scale_rotated = min(target_w / h, target_h / w)
    if scale_rotated > scale_normal:
        print("🔄 Rotating Image for Better Fit")
        img = img.rotate(90, expand=True)
    
    img = ImageOps.pad(img, CONFIG["TARGET_SIZE"], color=(255, 255, 255))
    img = img.quantize(palette=palette_image)
    print(f"✅ Image Processed. Final Size: {img.size}")
    return img

def update_display(image_source=None):
    """
    Update the display with an image.
    If image_source is None, fetch a random image using get_random_image().
    """
    if image_source is None:
        print("No image specified, fetching a random image...")
        image_source = get_random_image()
        if image_source is None:
            print("❌ No image available to update.")
            return
    img = preprocess_image(image_source)
    if img is None:
        print("❌ Failed to process image.")
        return
    print("📡 Updating display with new image...")
    buffer = epd.getbuffer(img)
    epd.display(buffer)
    print("✅ Display updated.")

def clear_display():
    """Clear the display."""
    print("📡 Clearing display...")
    epd.Clear()
    print("✅ Display cleared.")

# --- Socket Server Handler ---

class EpaperDaemonHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(1024).strip()
            if not data:
                return
            command = data.decode('utf-8').strip()
            print(f"Received command: {command}")
            parts = command.split(maxsplit=1)
            if parts[0].upper() == "UPDATE":
                if len(parts) > 1:
                    # Use the provided image path.
                    update_display(parts[1])
                else:
                    update_display()
                self.request.sendall(b"OK\n")
            elif parts[0].upper() == "CLEAR":
                clear_display()
                self.request.sendall(b"OK\n")
            else:
                print(f"Unknown command: {command}")
                self.request.sendall(b"ERROR: Unknown command\n")
        except Exception as e:
            print(f"Error handling command: {e}")
            self.request.sendall(b"ERROR: Exception occurred\n")

# --- Threaded TCP Server Setup ---

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 9999  # Listen on all interfaces
    server = ThreadedTCPServer((HOST, PORT), EpaperDaemonHandler)
    print(f"Persistent ePaper daemon running on {HOST}:{PORT}. Waiting for commands...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Daemon interrupted, shutting down.")
        server.shutdown()

