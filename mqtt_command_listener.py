#!/usr/bin/env python3
import os
import json
import logging
import subprocess
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# ✅ Load environment variables from .env and .secrets
load_dotenv()
if os.path.exists(".secrets"):
    load_dotenv(".secrets")

# Configure logging
logging.basicConfig(level=logging.INFO)

# ✅ MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "homeassistant.local")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", None)
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "epaper_frame")
IMAGE_DIR = "/mnt/photos"

def run_command(command):
    """Helper function to execute shell commands."""
    try:
        subprocess.run(command, shell=True)
    except Exception as e:
        logging.error(f"❌ Failed to run command {command}: {e}")

def on_message(client, userdata, msg):
    """Handle incoming MQTT messages for controlling the ePaper frame."""
    payload = msg.payload.decode("utf-8").strip()
    logging.info(f"📥 Received MQTT command: {msg.topic} → {payload}")

    if payload == "shutdown":
        logging.info("🛑 Shutting down system via MQTT...")
        run_command("sudo shutdown now")
    elif payload == "display":
        logging.info("📺 Running display.py via MQTT...")
        run_command("python3 /home/kenneth/epaper-frame/display.py")
    elif payload.startswith("set_image:"):
        image_name = payload.replace("set_image:", "").strip()
        image_path = os.path.join(IMAGE_DIR, image_name)

        if os.path.exists(image_path):
            logging.info(f"🖼️ Setting display to {image_name} via MQTT...")
            run_command(f"python3 /home/kenneth/epaper-frame/display.py --image '{image_path}'")
        else:
            logging.error(f"❌ Image not found: {image_path}")
    else:
        logging.warning(f"⚠️ Unknown command received: {payload}")

def mqtt_listen():
    """Listen for MQTT commands (shutdown, display, set_image)."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.subscribe(f"{MQTT_TOPIC_PREFIX}/command")
        logging.info(f"📡 Listening for MQTT commands on {MQTT_TOPIC_PREFIX}/command...")
        client.loop_forever()
    except Exception as e:
        logging.error(f"❌ Failed to start MQTT listener: {e}")

if __name__ == "__main__":
    mqtt_listen()
