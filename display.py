#path ./display.py

import time
import importlib
import io
from PIL import Image, ImageOps
from config import CONFIG
from image_source import get_random_image

# Import appropriate ePaper display driver dynamically
if CONFIG["USE_SIMULATOR"]:
    from epd_emulator import epdemulator
    USE_TKINTER = CONFIG.get("USE_TKINTER", False)  # Set this in .env (True for GUI, False for Flask)
    
    print(f"Using EPD Emulator ({'Tkinter' if USE_TKINTER else 'Flask'} Mode)")
    epd = epdemulator.EPD(
        config_file=CONFIG["DISPLAY_MODEL"],
        use_tkinter=USE_TKINTER,
        use_color=True,
        update_interval=5,
        reverse_orientation=False
    )
else:
    print(f"Using real Waveshare ePaper display: {CONFIG['DISPLAY_MODEL']}")
    epd_module = importlib.import_module(f"waveshare_epd.{CONFIG['DISPLAY_MODEL']}")
    epd = epd_module.EPD()

# Initialize ePaper display
epd.init()
epd.Clear(255)  # Provide required color argument

# Define 7-color palette
palette_image = Image.new("P", (1, 1))
palette_image.putpalette((
    0, 0, 0, 255, 255, 255, 0, 255, 0, 0, 0, 255, 255, 0, 0, 255, 255, 0, 255, 128, 0
) + (0, 0, 0) * 249)

def preprocess_image(image_data):
    """Process image for display, resizing, rotating, and quantizing."""
    try:
        # Ensure `image_data` is an Image object
        if isinstance(image_data, str):  # If it's a file path, open it
            img = Image.open(image_data)
        elif isinstance(image_data, io.BytesIO):  # If streamed from Google Drive
            img = Image.open(image_data)
        else:
            raise ValueError("Unsupported image format")

    except Exception as e:
        print(f"Error opening image: {e}")
        return None

    if img.mode in ('RGBA', 'LA'):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    else:
        img = img.convert("RGB")

    img = ImageOps.exif_transpose(img)

    # Rotate for better fit
    w, h = img.size
    target_w, target_h = CONFIG["TARGET_SIZE"]
    scale_normal = min(target_w / w, target_h / h)
    scale_rotated = min(target_w / h, target_h / w)
    if scale_rotated > scale_normal:
        img = img.rotate(90, expand=True)

    img = ImageOps.pad(img, CONFIG["TARGET_SIZE"], color=(255, 255, 255))
    img = img.quantize(palette=palette_image)

    return img

def main():
    """Main function to handle image selection, processing, and display."""
    print(f"Using display: {CONFIG['DISPLAY_MODEL']}, Resolution: {CONFIG['TARGET_SIZE']}, Simulator: {CONFIG['USE_SIMULATOR']}")

    image_data = get_random_image()
    if image_data is None:
        print("No image to display. Exiting.")
        return

    img = preprocess_image(image_data)
    if img is None:
        print("Failed to preprocess image. Exiting.")
        return

    # Convert the processed image into the display buffer
    if CONFIG["USE_SIMULATOR"]:
        epd.paste_image(img, (0, 0, CONFIG["TARGET_SIZE"][0], CONFIG["TARGET_SIZE"][1]))  # Pass actual `Image` object
        epd.display(epd.get_frame_buffer(epd.draw))  # Emulator expects a draw buffer
        print("Emulator updated.")
    else:
        buffer = epd.getbuffer(img)
        epd.display(buffer)

    if not CONFIG["USE_SIMULATOR"]:
        time.sleep(5)
        epd.sleep()
        print("Scheduling shutdown in 5 minutes. To cancel, run: sudo shutdown -c")
        # subprocess.call(["sudo", "shutdown", "-h", "+5"])

if __name__ == "__main__":
    main()
