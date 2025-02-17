#!/bin/bash

# Define paths
PROJECT_DIR="$(dirname "$(realpath "$0")")"
LOG_FILE="/mnt/photos/epaper_logs.txt"

# Ensure the log file exists
touch "$LOG_FILE"

echo "🚀 Running ePaper update and display script..." | tee -a "$LOG_FILE"
cd "$PROJECT_DIR" || { echo "❌ Failed to navigate to project directory." | tee -a "$LOG_FILE"; exit 1; }

# Update the PiSugar auto wake time
echo "⏳ Setting next wake time..." | tee -a "$LOG_FILE"
/home/kenneth/epaper-frame/update_wake_time.sh >> "$LOG_FILE" 2>&1

# Run update script
echo "🔄 Updating project..." | tee -a "$LOG_FILE"
/home/kenneth/epaper-frame/update.sh >> "$LOG_FILE" 2>&1

# Make sure update_wake_time.sh is executable
chmod +x /home/kenneth/epaper-frame/update_wake_time.sh >> "$LOG_FILE" 2>&1

# Make sure update_to_drive.sh is executable
chmod +x /home/kenneth/epaper-frame/update_to_drive.sh >> "$LOG_FILE" 2>&1

# Run display script
echo "📺 Starting display.py..." | tee -a "$LOG_FILE"
python display.py >> "$LOG_FILE" 2>&1

echo "✅ Done!" | tee -a "$LOG_FILE"

# Upload the log file to Google Drive (append instead of replacing)
echo "☁️ Uploading log file to Google Drive..." | tee -a "$LOG_FILE"
python /home/kenneth/epaper-frame/upload_to_drive.py "$LOG_FILE" >> "$LOG_FILE" 2>&1
echo "✅ Log file uploaded!" | tee -a "$LOG_FILE"
