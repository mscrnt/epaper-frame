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
LOG_FILE = "/mnt/photos/epaper_logs.txt"

def run_command(command):
    """Helper function to execute shell commands."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.stdout.strip() if result.stdout else None
    except Exception as e:
        logging.error(f"❌ Failed to run command {command}: {e}")
        return None

def get_last_displayed_image():
    """Extract the last image displayed from the log file, preserving spaces."""
    if not os.path.exists(LOG_FILE):
        logging.error(f"❌ Log file not found: {LOG_FILE}")
        return "Unknown"

    last_image = "Unknown"
    try:
        with open(LOG_FILE, "r") as log_file:
            for line in log_file:
                if "🖼️ Last Image Displayed:" in line:
                    last_image = line.split("🖼️ Last Image Displayed: ")[1].strip().strip('"')  # ✅ Preserve full filename

    except Exception as e:
        logging.error(f"❌ Error reading log file: {e}")

    return last_image


def clean_response(response, prefix):
    """Remove response prefix (e.g., 'battery: 77.51571' → '77.52%')"""
    if response and response.startswith(prefix):
        return response.replace(prefix, "").strip()
    return response

def get_battery_status():
    """Retrieve and clean battery status from PiSugar."""
    battery = clean_response(run_command("echo 'get battery' | nc -q 0 127.0.0.1 8423"), "battery:")
    battery_v = clean_response(run_command("echo 'get battery_v' | nc -q 0 127.0.0.1 8423"), "battery_v:")
    battery_i = clean_response(run_command("echo 'get battery_i' | nc -q 0 127.0.0.1 8423"), "battery_i:")
    battery_charging = clean_response(run_command("echo 'get battery_charging' | nc -q 0 127.0.0.1 8423"), "battery_charging:")
    battery_power_plugged = clean_response(run_command("echo 'get battery_power_plugged' | nc -q 0 127.0.0.1 8423"), "battery_power_plugged:")

    return {
        "charge": f"{float(battery):.2f}%" if battery else "Unknown",
        "voltage": f"{float(battery_v):.2f}V" if battery_v else "Unknown",
        "current": f"{float(battery_i):.2f}A" if battery_i else "Unknown",
        "charging": battery_charging,
        "power_plugged": battery_power_plugged
    }

def publish_mqtt(topic, payload, retain=True):
    """Send MQTT message to Home Assistant using discovery format."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # ✅ Use correct API version

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        full_topic = f"{MQTT_TOPIC_PREFIX}/{topic}"
        discovery_topic = f"homeassistant/sensor/{MQTT_TOPIC_PREFIX}_{topic}/config"  # ✅ Home Assistant format
        
        # ✅ Publish Discovery message (only needed once per device)
        discovery_payload = {
            "name": f"{MQTT_TOPIC_PREFIX} {topic.replace('_', ' ').title()}",
            "state_topic": full_topic,
            "unique_id": f"{MQTT_TOPIC_PREFIX}_{topic}",
            "device": {
                "identifiers": [MQTT_TOPIC_PREFIX],
                "name": MQTT_TOPIC_PREFIX,
                "model": "Raspberry Pi ePaper Frame",
                "manufacturer": "Mscrnt LLC",
            }
        }
        
        client.publish(discovery_topic, json.dumps(discovery_payload), retain=True)  # ✅ Auto discovery config
        client.publish(full_topic, json.dumps(payload, ensure_ascii=False), retain=retain)  # ✅ Send actual data

        logging.info(f"✅ Sent MQTT update to {full_topic}: {payload}")
        client.disconnect()
    except Exception as e:
        logging.error(f"❌ Failed to send MQTT message: {e}")


if __name__ == "__main__":
    # ✅ Retrieve values automatically
    last_image = get_last_displayed_image()
    battery_status = get_battery_status()

    # ✅ Send MQTT updates
    publish_mqtt("last_image", {"image": last_image})
    publish_mqtt("battery_status", battery_status)
