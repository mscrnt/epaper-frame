### **📄 README.md - ePaper Frame for Raspberry Pi**
This project is designed to **display images on an ePaper display** using a **Raspberry Pi**. It supports **Google Drive image retrieval**, a **Tkinter-based simulator**, and an **automatic shutdown feature** for power efficiency.  

The system can be set up to **wake on an event**, display an image, and **shut down** after execution. Users can prevent shutdown by **updating the repo** or manually canceling shutdown.

---

## **🛠 Features**
✔ **Supports Waveshare ePaper displays**  
✔ **Simulated ePaper display (EPD Emulator)**  
✔ **Retrieves images from local storage or Google Drive**  
✔ **Tkinter UI mode for GUI simulation**  
✔ **Automatic shutdown after displaying the image** *(optional)*  
✔ **Over-the-Air (OTA) updates via Git**  

---

## **📂 Project Structure**
```
epepar-frame/
│── epd_emulator/              # EPD Emulator for Tkinter or Flask
│   ├── epdemulator.py         # Handles EPD simulation with Tkinter & Flask
│── waveshare_epd/             # Drivers for real Waveshare ePaper displays
│── images/                    # Local folder for images (if using local storage)
│── config.py                  # Loads settings from .env & CLI arguments
│── display.py                 # Main script that processes & displays images
│── image_source.py            # Handles fetching images from local or Google Drive
│── update.sh                  # Fetches latest updates from GitHub
│── run_update_and_display.sh  # Updates project & runs display.py
│── .env                       # Environment variables for configuration
│── .secrets                   # Secure storage for sensitive values (Google Drive)
│── README.md                  # This documentation
```

---

## **📜 Credits**
This project **uses and extends the EPD Emulator** from [EPD-Emulator](https://github.com/infinition/EPD-Emulator) by [infinition](https://github.com/infinition). The emulator allows for **Tkinter- and Flask-based simulation of ePaper displays**, making it an excellent tool for development without physical hardware.

---

## **🚀 Installation on Raspberry Pi**
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/YOUR-USERNAME/epepar-frame.git
cd epepar-frame
```
> **🔹 Important:** Replace `YOUR-USERNAME` with **your own GitHub repo** if you forked the project.

---

### **2️⃣ Install Dependencies**
Install required packages:
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```
Create a **Python virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

---

### **3️⃣ Configure `.env` File**
Create a `.env` file in the project root:
```
IMAGE_SOURCE=drive  # Options: local, drive
GOOGLE_SERVICE_ACCOUNT=credentials.json
LOCAL_IMAGE_DIR=./images
DISPLAY=epd5in65f  # Default display
USE_SIMULATOR=true  # Set to "true" to use the emulator
USE_TKINTER=false   # Set to "true" for GUI mode
SHUTDOWN_AFTER_RUN=true  # Set to "true" to shutdown after displaying the image
```

> **🛠 Need to prevent shutdown?** Update `.env` with `SHUTDOWN_AFTER_RUN=false` and reboot the Pi.

---

### **4️⃣ Set Up Google Drive (Optional)**
If using Google Drive:
1. **Enable Google Drive API**: [Google Cloud Console](https://console.cloud.google.com/)
2. **Download `credentials.json`** and place it in the project root.
3. Add your **Google Drive Folder ID** to `.secrets`:
   ```
   GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
   ```

---

## **🖥️ Running the Display Script**
### **📌 Manually Run**
```bash
python display.py
```
This will:
- Fetch an image (from local storage or Google Drive)
- Process it for the **ePaper display** or **simulator**
- Display the image
- Shutdown the Pi if `SHUTDOWN_AFTER_RUN=true`

### **📌 Prevent Shutdown**
To prevent automatic shutdown:
```bash
sudo shutdown -c
```
Or update `.env`:
```bash
nano .env
# Change the SHUTDOWN_AFTER_RUN variable
SHUTDOWN_AFTER_RUN=false
```

---

## **🔄 Automating Updates & Execution**
### **📌 `update.sh` (Fetch latest updates from GitHub)**
This script updates the project.  
Users should **modify it to point to their own GitHub repo**.

```bash
#!/bin/bash

# Define the repo URL and project directory
REPO_URL="https://github.com/YOUR-USERNAME/epepar-frame.git"
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

echo "✅ Update complete!"
```
Run manually:
```bash
./update.sh
```

---

### **📌 `run_update_and_display.sh` (Update and run display.py)**
```bash
#!/bin/bash

# Define the project directory (auto-detects the script location)
PROJECT_DIR="$(dirname "$(realpath "$0")")"

echo "🚀 Running ePaper update and display script..."
cd "$PROJECT_DIR" || { echo "❌ Failed to navigate to project directory."; exit 1; }

# Run update script
echo "🔄 Updating project..."
./update.sh

# Run display script
echo "📺 Starting display.py..."
python display.py

echo "✅ Done!"
```
Run manually:
```bash
./run_update_and_display.sh
```

---

### **🔁 Automating with `cron`**
To set the Raspberry Pi to **wake on event**, display an image, and **shut down**, schedule the script via `cron`:

```bash
crontab -e
```
Add this line:
```
@reboot /bin/bash /path/to/epepar-frame/run_update_and_display.sh
```
> **Note:** Replace `/path/to/epepar-frame/` with your actual project path.

This will:
1. **Update the repository** on boot.
2. **Fetch new images**.
3. **Display an image**.
4. **Shutdown (if `SHUTDOWN_AFTER_RUN=true`)**.

---

## **🔧 Configuration Options**
| **Variable**         | **Description**                                      | **Default** |
|----------------------|------------------------------------------------------|------------|
| `IMAGE_SOURCE`       | `local` (local storage) or `drive` (Google Drive)    | `local`    |
| `GOOGLE_SERVICE_ACCOUNT` | JSON file for Google Drive authentication       | `credentials.json` |
| `LOCAL_IMAGE_DIR`    | Folder for locally stored images                     | `./images` |
| `DISPLAY`           | Selects the ePaper display model                      | `epd5in65f` |
| `USE_SIMULATOR`      | `true` (use emulator) or `false` (use real display)  | `true`     |
| `USE_TKINTER`        | `true` (Tkinter UI mode) or `false` (Flask)          | `false`    |
| `SHUTDOWN_AFTER_RUN` | `true` (auto shutdown) or `false` (stay on)         | `true`     |

---

🚀 **Enjoy your ePaper display!** Special thanks to **[EPD-Emulator](https://github.com/infinition/EPD-Emulator)** for the emulator code. 🔥