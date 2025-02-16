#!/usr/bin/python3
import os
import random
import subprocess
import time
from PIL import Image, ImageOps
from waveshare_epd import epd5in65f

# Directory containing raw images
RAW_DIR = "/mnt/photos"
# Target resolution for the display (width x height)
TARGET_SIZE = (600, 448)

# Create a palette image with the 7 supported colors:
palette_image = Image.new("P", (1, 1))
palette_image.putpalette((
    0, 0, 0,         # BLACK
    255, 255, 255,   # WHITE
    0, 255, 0,       # GREEN
    0, 0, 255,       # BLUE
    255, 0, 0,       # RED
    255, 255, 0,     # YELLOW
    255, 128, 0      # ORANGE
) + (0, 0, 0) * 249)

def preprocess_image_in_memory(image_path):
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Error opening {image_path}: {e}")
        return None

    # Convert palette images with transparency to RGBA.
    if img.mode == 'P' and 'transparency' in img.info:
        img = img.convert("RGBA")

    # Composite images with an alpha channel onto a white background.
    if img.mode in ('RGBA', 'LA'):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    else:
        img = img.convert("RGB")

    # Adjust orientation using EXIF data.
    img = ImageOps.exif_transpose(img)

    # Determine if rotating 90° provides a better fit.
    w, h = img.size
    target_w, target_h = TARGET_SIZE
    scale_normal = min(target_w / w, target_h / h)
    scale_rotated = min(target_w / h, target_h / w)
    if scale_rotated > scale_normal:
        img = img.rotate(90, expand=True)

    # Resize and pad the image to fill the target dimensions.
    img = ImageOps.pad(img, TARGET_SIZE, color=(255, 255, 255))
    # Convert the image to the limited palette.
    img = img.quantize(palette=palette_image)
    return img

# Define valid image file extensions.
valid_extensions = ('.bmp', '.png', '.jpg', '.jpeg', '.jfif', '.webp')

def get_image_files():
    return [
        os.path.join(RAW_DIR, f)
        for f in os.listdir(RAW_DIR)
        if f.lower().endswith(valid_extensions)
    ]

# Wait up to 5 minutes if no images are found.
wait_time = 300  # total wait time in seconds
interval = 10    # check interval in seconds
elapsed = 0

image_files = get_image_files()
if not image_files:
    print("No image files found in", RAW_DIR, "- waiting up to 5 minutes for USB drive to be populated.")
    while elapsed < wait_time:
        time.sleep(interval)
        elapsed += interval
        image_files = get_image_files()
        if image_files:
            print("Image files detected, proceeding with processing.")
            break

if not image_files:
    print("Still no images after 5 minutes. Nothing to display.")
else:
    selected_image = random.choice(image_files)
    print("Selected image:", selected_image)

    img = preprocess_image_in_memory(selected_image)
    if img is None:
        exit(1)

    # Initialize the ePaper display.
    epd = epd5in65f.EPD()
    epd.init()
    epd.Clear()

    # Convert the processed image into the display buffer.
    buffer = epd.getbuffer(img)
    # Display the image on the ePaper.
    epd.display(buffer)
    # Allow some time for the display update.
    time.sleep(5)
    epd.sleep()

# Now that all processing is complete, schedule shutdown in 5 minutes.
print("Scheduling shutdown in 5 minutes. To cancel, run: sudo shutdown -c")
subprocess.call(["sudo", "shutdown", "-h", "+5"])
