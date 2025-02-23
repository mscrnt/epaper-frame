#!/bin/bash

# Define paths
PROJECT_DIR="$(dirname "$(realpath "$0")")"
LOG_FILE="/mnt/photos/epaper_logs.txt"
MQTT_SCRIPT="/home/kenneth/epaper-frame/mqtt_update.py"

# Ensure the log file exists
touch "$LOG_FILE"

echo "🚀 Running ePaper update and display script..." | tee -a "$LOG_FILE"
cd "$PROJECT_DIR" || { echo "❌ Failed to navigate to project directory." | tee -a "$LOG_FILE"; exit 1; }

# Update the PiSugar auto wake time
chmod +x /home/kenneth/epaper-frame/update_wake_time.sh >> "$LOG_FILE" 2>&1
echo "⏳ Setting next wake time..." | tee -a "$LOG_FILE"
/home/kenneth/epaper-frame/update_wake_time.sh >> "$LOG_FILE" 2>&1

# Run update script
echo "🔄 Updating project..." | tee -a "$LOG_FILE"
/home/kenneth/epaper-frame/update.sh >> "$LOG_FILE" 2>&1

# Run display script
echo "📺 Starting display.py..." | tee -a "$LOG_FILE"
python display.py >> "$LOG_FILE" 2>&1

# ✅ Run MQTT update script (handles last image & battery automatically)
python "$MQTT_SCRIPT"

# Upload the log file to Google Drive
echo "☁️ Uploading log file to Google Drive..." | tee -a "$LOG_FILE"
python /home/kenneth/epaper-frame/upload_to_drive.py "$LOG_FILE" >> "$LOG_FILE" 2>&1
echo "✅ Log file uploaded!" | tee -a "$LOG_FILE"
