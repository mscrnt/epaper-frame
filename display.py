import time
import importlib
import io
import subprocess
from PIL import Image, ImageOps
from config import CONFIG
from image_source import get_random_image
import os

# Import appropriate ePaper display driver dynamically
if CONFIG["USE_SIMULATOR"]:
    from epd_emulator import epdemulator
    USE_TKINTER = CONFIG["USE_TKINTER"]  

    print(f"📡 Using EPD Emulator ({'Tkinter' if USE_TKINTER else 'Flask'} Mode)")
    epd = epdemulator.EPD(
        config_file=CONFIG["DISPLAY_MODEL"],
        use_tkinter=USE_TKINTER,
        use_color=True,
        update_interval=5,
        reverse_orientation=False
    )
else:
    print(f"📡 Using real Waveshare ePaper display: {CONFIG['DISPLAY_MODEL']}")
    epd_module = importlib.import_module(f"waveshare_epd.{CONFIG['DISPLAY_MODEL']}")
    epd = epd_module.EPD()

# Initialize ePaper display
print("✅ Initializing EPD Display...")
epd.init()

# Correct the `Clear()` call based on simulator or real hardware
if CONFIG["USE_SIMULATOR"]:
    epd.Clear(255)  # Simulator requires a color argument
else:
    epd.Clear()  # Real Waveshare displays take no arguments

print("✅ EPD Display Cleared")

# Define 7-color palette
palette_image = Image.new("P", (1, 1))
palette_image.putpalette((
    0, 0, 0, 255, 255, 255, 0, 255, 0, 0, 0, 255, 255, 0, 0, 255, 255, 0, 255, 128, 0
) + (0, 0, 0) * 249)

def check_ssh_sessions():
    """Check if any active SSH sessions exist."""
    ssh_check = subprocess.run(["who"], capture_output=True, text=True)
    return "pts/" in ssh_check.stdout  # Active SSH sessions show up as pts/ sessions

def preprocess_image(image_data):
    """Process image for display, resizing, rotating, and quantizing."""
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

    # Rotate for better fit
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

LOG_FILE = "/mnt/photos/epaper_logs.txt"

def log_displayed_image(image_path):
    """Overwrite the last displayed image entry in the log file."""
    log_lines = []

    # Read existing log file, excluding previous "Last Image Displayed" entries
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as log_file:
            log_lines = [line for line in log_file if "🖼️ Last Image Displayed:" not in line]

    # Append new last image entry
    log_lines.append(f"🖼️ Last Image Displayed: {image_path}\n")

    # Overwrite log file with the updated list
    with open(LOG_FILE, "w") as log_file:
        log_file.writelines(log_lines)

    print(f"🖼️ Last Image Updated: {image_path}")


def main():
    """Main function to handle image selection, processing, and display."""
    print(f"📺 Using Display: {CONFIG['DISPLAY_MODEL']}, Resolution: {CONFIG['TARGET_SIZE']}, Simulator: {CONFIG['USE_SIMULATOR']}")

    image_data = get_random_image()
    if image_data is None:
        print("❌ No image to display. Exiting.")
        return
    
    # Log the displayed image
    if isinstance(image_data, str):
        log_displayed_image(image_data)

    img = preprocess_image(image_data)
    if img is None:
        print("❌ Failed to preprocess image. Exiting.")
        return

    # Convert the processed image into the display buffer
    if CONFIG["USE_SIMULATOR"]:
        print("🔄 Pasting Image onto EPD Emulator...")
        epd.paste_image(img, (0, 0, CONFIG["TARGET_SIZE"][0], CONFIG["TARGET_SIZE"][1]))
        print("📡 Displaying Image on Emulator...")
        epd.display(img)
        print("✅ Emulator Updated.")
    else:
        print("📡 Displaying Image on Real EPD Display...")
        buffer = epd.getbuffer(img)
        epd.display(buffer)

    # Shutdown logic with SSH failsafe
    if CONFIG["SHUTDOWN_AFTER_RUN"]:
        if check_ssh_sessions():
            print("🚨 Active SSH session detected! Preventing shutdown.")
            print("🔄 System will remain ON for maintenance.")
        else:
            print("⏳ Scheduling Shutdown in 5 Minutes. To cancel, run: sudo shutdown -c")
            subprocess.call(["sudo", "shutdown", "-h", "+1"])
    else:
        print("🟢 SHUTDOWN_AFTER_RUN is disabled. Display will remain on.")

if __name__ == "__main__":
    main()
