#!/bin/bash

# Define the repo URL and project directory
REPO_URL="https://github.com/mscrnt/epepar-frame.git"
PROJECT_DIR="$(dirname "$(realpath "$0")")"

echo "📡 Pulling latest updates for the EPD project..."
cd "$PROJECT_DIR" || { echo "❌ Failed to navigate to project directory."; exit 1; }

# Ensure Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if the project is already a git repo
if [ ! -d .git ]; then
    echo "🚀 Cloning repository..."
    git clone "$REPO_URL" "$PROJECT_DIR"
else
    echo "🔄 Pulling latest changes..."
    git reset --hard origin/main  # Ensure a clean update
    git pull origin main
fi

# Make sure the config directory exists
if [ ! -d "$PROJECT_DIR/config" ]; then
    echo "⚠ Config directory missing. Creating it..."
    mkdir -p "$PROJECT_DIR/config"
fi

# Restart the display service (optional)
if systemctl list-units --full -all | grep -q "epaper.service"; then
    echo "🔄 Restarting ePaper display service..."
    sudo systemctl restart epaper.service
else
    echo "⚠ No epaper.service found. Skipping restart."
fi

echo "✅ Update complete!"
