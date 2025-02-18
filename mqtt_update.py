#!/usr/bin/env python3
import os
import json
import logging
import subprocess
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# ✅ Load environment variables
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
LOG_FILE = os.getenv("LOG_FILE", "/mnt/photos/epaper_logs.txt")

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
                    last_image = line.split("🖼️ Last Image Displayed: ")[1].strip().strip('"')

    except Exception as e:
        logging.error(f"❌ Error reading log file: {e}")

    return last_image

def get_pisugar_status():
    """Retrieve all PiSugar-related metrics."""
    commands = {
        "firmware_version": "get firmware_version",
        "battery": "get battery",
        "battery_i": "get battery_i",
        "battery_v": "get battery_v",
        "battery_charging": "get battery_charging",
        "battery_input_protect": "get battery_input_protect_enabled",
        "model": "get model",
        "battery_led_amount": "get battery_led_amount",
        "battery_power_plugged": "get battery_power_plugged",
        "battery_charging_range": "get battery_charging_range",
        "battery_allow_charging": "get battery_allow_charging",
        "battery_output_enabled": "get battery_output_enabled",
        "rtc_time": "get rtc_time",
        "rtc_alarm_enabled": "get rtc_alarm_enabled",
        "rtc_alarm_time": "get rtc_alarm_time",
        "alarm_repeat": "get alarm_repeat",
        "button_enable": "get button_enable",
        "safe_shutdown_level": "get safe_shutdown_level",
        "safe_shutdown_delay": "get safe_shutdown_delay",
        "auth_username": "get auth_username",
        "anti_mistouch": "get anti_mistouch",
        "soft_poweroff": "get soft_poweroff",
        "temperature": "get temperature",
        "input_protect": "get input_protect",
    }

    status = {}
    for key, command in commands.items():
        response = run_command(f"echo '{command}' | nc -q 0 127.0.0.1 8423")
        status[key] = response if response else "Unknown"

    return status

def publish_mqtt(topic, payload, retain=True):
    """Send MQTT message to Home Assistant using discovery format."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)

        full_topic = f"{MQTT_TOPIC_PREFIX}/{topic}"
        discovery_topic = f"homeassistant/sensor/{MQTT_TOPIC_PREFIX}_{topic}/config"

        # ✅ Determine sensor type (binary_sensor or regular sensor)
        sensor_type = "sensor"  # Default to sensor
        if "charging" in topic or "plugged" in topic or "poweroff" in topic:
            sensor_type = "binary_sensor"

        # ✅ Publish Discovery message
        discovery_payload = {
            "name": f"{MQTT_TOPIC_PREFIX} {topic.replace('_', ' ').title()}",
            "state_topic": full_topic,
            "unique_id": f"{MQTT_TOPIC_PREFIX}_{topic}",
            "device": {
                "identifiers": [MQTT_TOPIC_PREFIX],
                "name": MQTT_TOPIC_PREFIX,
                "model": "Raspberry Pi ePaper Frame",
                "manufacturer": "Mscrnt LLC",
            },
        }

        if sensor_type == "binary_sensor":
            discovery_payload["payload_on"] = "true"
            discovery_payload["payload_off"] = "false"

        client.publish(discovery_topic, json.dumps(discovery_payload), retain=True)
        client.publish(full_topic, payload, retain=retain)

        logging.info(f"✅ Sent MQTT update to {full_topic}: {payload}")
        client.disconnect()
    except Exception as e:
        logging.error(f"❌ Failed to send MQTT message: {e}")

if __name__ == "__main__":
    # ✅ Retrieve values automatically
    last_image = get_last_displayed_image()
    pisugar_status = get_pisugar_status()

    # ✅ Send last displayed image
    publish_mqtt("last_image", last_image)

    # ✅ Send each PiSugar metric separately
    for key, value in pisugar_status.items():
        publish_mqtt(f"pisugar_{key}", value)
