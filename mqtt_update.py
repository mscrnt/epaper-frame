#!/usr/bin/env python3
import os
import sys
import json
import logging
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import subprocess

# ✅ Load environment variables from .env and .secrets
load_dotenv()
if os.path.exists(".secrets"):
    load_dotenv(".secrets")

# Configure logging
logging.basicConfig(level=logging.INFO)

# ✅ MQTT Configuration (from .env or .secrets)
MQTT_BROKER = os.getenv("MQTT_BROKER", "homeassistant.local")  # Home Assistant server address
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))  # Default MQTT port
MQTT_USERNAME = os.getenv("MQTT_USERNAME", None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", None)
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "epaper_frame")  # Base topic

def get_battery_status():
    """Retrieve battery status from PiSugar."""
    try:
        result = subprocess.run(["echo", "get battery", "|", "nc", "-q", "0", "127.0.0.1", "8423"], capture_output=True, text=True, shell=True)
        return result.stdout.strip() if result.stdout else "Unknown"
    except Exception as e:
        logging.error(f"❌ Failed to get battery status: {e}")
        return "Error"

def publish_mqtt(topic, payload):
    """Send MQTT message to Home Assistant."""
    client = mqtt.Client()
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        full_topic = f"{MQTT_TOPIC_PREFIX}/{topic}"
        client.publish(full_topic, json.dumps(payload), retain=True)
        logging.info(f"✅ Sent MQTT update to {full_topic}: {payload}")
        client.disconnect()
    except Exception as e:
        logging.error(f"❌ Failed to send MQTT message: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        logging.error("❌ Usage: mqtt_update.py <topic> <json_payload>")
        sys.exit(1)

    topic = sys.argv[1]
    payload = json.loads(sys.argv[2])
    publish_mqtt(topic, payload)
