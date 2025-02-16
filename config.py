# path: ./config.py

import argparse
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supported ePaper displays and their resolutions
EPD_SCREENS = {
    "epd1in54": (200, 200),
    "epd2in7": (264, 176),
    "epd2ing": (152, 152),
    "epd2in13": (250, 122),
    "epd2in13v2": (250, 122),
    "epd2in66": (296, 152),
    "epd3in7": (416, 240),
    "epd3in52": (400, 300),
    "epd4in2": (400, 300),
    "epd4in3": (800, 600),
    "epd5in65": (600, 448),  # Emulator uses this
    "epd5in65f": (600, 448), # Real ePaper uses this
    "epd5in83": (648, 480),
    "epd6in0": (800, 600),
    "epd6in2": (1448, 1072),
    "epd7in5": (800, 480),
    "epd9in7": (1200, 825),
    "epd10in3": (1872, 1404),
    "epd11in6": (2560, 1600),
    "epd12in48": (1304, 984),
}

def get_config():
    """Parses command-line arguments and environment variables"""
    parser = argparse.ArgumentParser(description="ePaper Frame Configuration")
    parser.add_argument("--source", choices=["local", "drive"], default=os.getenv("IMAGE_SOURCE", "local"),
                        help="Image source (local storage or Google Drive)")
    parser.add_argument("--display", choices=EPD_SCREENS.keys(), default=os.getenv("DISPLAY", "epd5in65f"),
                        help="Select the ePaper display model")
    parser.add_argument("--simulator", action="store_true",
                        help="Use the EPD Emulator instead of a real ePaper display")

    args = parser.parse_args()

    # Determine if using the simulator
    use_simulator = args.simulator or os.getenv("USE_SIMULATOR", "false").lower() == "true"

    # Automatically adjust display key based on simulator mode
    if use_simulator and args.display == "epd5in65f":
        display_model = "epd5in65"  # Use emulator key
    elif not use_simulator and args.display == "epd5in65":
        display_model = "epd5in65f"  # Use real ePaper key
    else:
        display_model = args.display

    return {
        "IMAGE_SOURCE": args.source,
        "DISPLAY_MODEL": display_model,
        "TARGET_SIZE": EPD_SCREENS[display_model],
        "USE_SIMULATOR": use_simulator,
        "LOCAL_IMAGE_DIR": os.getenv("LOCAL_IMAGE_DIR", "/mnt/photos"),
        "DRIVE_FOLDER_ID": os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""),
        "SERVICE_ACCOUNT_FILE": os.getenv("GOOGLE_SERVICE_ACCOUNT", "credentials.json"),
    }

CONFIG = get_config()
