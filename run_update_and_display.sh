#!/bin/bash

# Define the project directory (auto-detects the script location)
PROJECT_DIR="$(dirname "$(realpath "$0")")"

echo "🚀 Running ePaper update and display script..."
cd "$PROJECT_DIR" || { echo "❌ Failed to navigate to project directory."; exit 1; }

# Update the PiSugar auto wake time
echo "⏳ Setting next wake time..."
./update_wake_time.sh

# Run update script
echo "🔄 Updating project..."
./update.sh

# Run display script
echo "📺 Starting display.py..."
python display.py

echo "✅ Done!"
