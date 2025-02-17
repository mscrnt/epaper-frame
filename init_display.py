#!/usr/bin/env python3
import sys
import importlib
from config import CONFIG

# Ensure this script is only used for production (real hardware)
if CONFIG.get("USE_SIMULATOR", False):
    sys.exit("Error: init_display.py is for production only. Disable simulator mode in your configuration.")

print(f"Using real ePaper display: {CONFIG['DISPLAY_MODEL']}")

# Import the appropriate driver module for the real hardware
epd_module = importlib.import_module(f"waveshare_epd.{CONFIG['DISPLAY_MODEL']}")
epd = epd_module.EPD()

print("Initializing display hardware...")
result = epd.init()
if result != 0:
    sys.exit("Display initialization failed.")

print("Clearing display to ready state...")
epd.Clear()

print("Display initialization complete.")
