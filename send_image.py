#!/usr/bin/env python3
import importlib
import io
from PIL import Image, ImageOps
from config import CONFIG
from image_source import get_random_image

# For production, we assume simulator mode is disabled.
print(f"📡 Using real Waveshare ePaper display: {CONFIG['DISPLAY_MODEL']}")
epd_module = importlib.import_module(f"waveshare_epd.{CONFIG['DISPLAY_MODEL']}")
epd = epd_module.EPD()

# NOTE: We assume the display is already initialized.
# Therefore, we do not call epd.init() or epd.Clear() here.

# Define 7-color palette
palette_image = Image.new("P", (1, 1))
palette_image.putpalette((
    0, 0, 0, 255, 255, 255, 0, 255, 0, 0, 0, 255, 255, 0, 0, 255, 255, 0, 255, 128, 0
) + (0, 0, 0) * 249)

def preprocess_image(image_data):
    """Process image for display: resizing, rotating, and quantizing."""
    print("🔄 Preprocessing Image...")
    try:
        if isinstance(image_data, str):
            print(f"📂 Opening Local Image: {image_data}")
            img = Image.open(image_data)
        elif isinstance(image_data, io.BytesIO):
            print("📡 Opening Image from Google Drive")
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

    # Rotate for better fit if needed.
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

def main():
    """Fetch, process, and send the image to the already-initialized display."""
    print(f"📺 Using Display: {CONFIG['DISPLAY_MODEL']}, Resolution: {CONFIG['TARGET_SIZE']}")
    image_data = get_random_image()
    if image_data is None:
        print("❌ No image to display. Exiting.")
        return

    img = preprocess_image(image_data)
    if img is None:
        print("❌ Failed to preprocess image. Exiting.")
        return

    print("📡 Sending image to Real EPD Display...")
    # For real hardware, convert the processed image into a display buffer and send it.
    buffer = epd.getbuffer(img)
    epd.display(buffer)
    print("✅ Image sent to display.")

if __name__ == "__main__":
    main()
