## **📄 README.md - ePaper Frame for Raspberry Pi**
This project enables a **Raspberry Pi** to display images on an **ePaper display**. It supports **Google Drive image retrieval**, a **simulated ePaper display**, and **power management** using a **PiSugar battery**.

The system can **wake on a schedule**, display an image, and **shut down** after execution. Users can also **control it via MQTT commands** from Home Assistant.

---

## **🛠 Features**
✔ **Supports Waveshare ePaper displays**  
✔ **Simulated ePaper display (EPD Emulator)**  
✔ **Retrieves images from local storage or Google Drive**  
✔ **Automated wake-up using PiSugar battery**  
✔ **Reports battery status via MQTT**  
✔ **Accepts MQTT commands for display updates**  
✔ **Over-the-Air (OTA) updates via Git**  

---

## **📂 Project Structure**
```
epepar-frame/
│── epd_emulator/              # EPD Emulator for Tkinter or Flask
│── waveshare_epd/             # Drivers for real Waveshare ePaper displays
│── images/                    # Local folder for images
│── config.py                  # Loads settings from .env & CLI arguments
│── display.py                 # Main script for processing & displaying images
│── image_source.py            # Fetches images from local or Google Drive
│── update.sh                  # Fetches latest updates from GitHub
│── update_wake_time.sh        # Updates PiSugar wake time
│── run_update_and_display.sh  # Runs updates & display.py
│── mqtt_update.py             # Sends battery status & last image to MQTT
│── mqtt_command_listener.py   # Listens for MQTT commands (shutdown, update display)
│── upload_to_drive.py         # Uploads logs to Google Drive
│── .env                       # Environment variables for configuration
│── .secrets                   # Secure storage for sensitive values (Google Drive)
│── README.md                  # This documentation
```

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
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git jq
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
MQTT_BROKER=homeassistant.local
MQTT_PORT=1883
MQTT_TOPIC_PREFIX=epaper_frame
```

> **🛠 Need to prevent shutdown?** Set `SHUTDOWN_AFTER_RUN=false` in `.env`.

---

### **3️⃣ Configure `.secrets` File**
Create a `.secrets` file in the project root:
```
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id (if using Google Drive)
GOOGLE_DRIVE_LOG_FOLDER_ID=your_log_folder_id (if using Google Drive)
MQTT_USERNAME=your_mqtt_username (if using MQTT)
MQTT_PASSWORD=your_mqtt_password (if using MQTT)
```

---
### **4️⃣ Configure Google Drive (Optional)**
If using Google Drive:
1. **Enable Google Drive API**: [Google Cloud Console](https://console.cloud.google.com/).
2. **Download `credentials.json`** and place it in the project root.
3. **Share the folder** with the service account email found in `credentials.json`.
4. **Set the folder ID** in `.secrets` file.

---

## **🔋 PiSugar Battery Setup**
This setup **requires PiSugar** with the **PiSugar server running**.

To check if the PiSugar server is running:
```bash
sudo systemctl status pisugar-server
```

Set the PiSugar **wake-up time** every **8 hours**:
```bash
/home/kenneth/epaper-frame/update_wake_time.sh
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

---

## **📡 MQTT Integration**
### **📤 Sends These MQTT Updates**
| **Topic**                 | **Payload Example**                            | **Description** |
|---------------------------|--------------------------------|----------------|
| `epaper_frame/last_image` | `{"image": "Last_image_displayed.jpg"}` | Last displayed image |
| `epaper_frame/battery_status` | `{"charge": "77.52%", "voltage": "3.80V", "current": "-1.05A", "charging": "false", "power_plugged": "true"}` | Battery status |

### **📥 Accepts These MQTT Commands**
| **Topic**                   | **Payload**           | **Action** |
|-----------------------------|----------------------|------------|
| `epaper_frame/command`       | `shutdown`          | Shuts down the Pi |
| `epaper_frame/command`       | `display`           | Runs `display.py` |
| `epaper_frame/command`       | `set_image: my_image.jpg` | Displays a specific image |

---
### **📌 Automate MQTT Services**
To run **MQTT updates & command listener** automatically:


---
#### **Create `mqtt_command_listener.service`**
```bash
sudo nano /etc/systemd/system/mqtt_command_listener.service
```
```
[Unit]
Description=E-Paper MQTT Command Listener
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/mqtt_command_listener.py
Restart=always
User=kenneth

[Install]
WantedBy=multi-user.target
```
> **🔹 Important:** Replace `/path/to/` with the **actual path** to your `mqtt_command_listener.py` file.

Or copy the mqtt_command_listener.service file from the project root to `/etc/systemd/system/`.

```bash
sudo cp mqtt_command_listener.service /etc/systemd/system/
```
Enable & start:
```bash
sudo systemctl enable mqtt_command_listener.service
sudo systemctl start mqtt_command_listener.service
```

---

### **📌 `run_update_and_display.sh` (Update and run display.py)**
This script runs the update, **fetches new images**, and **updates the display**.

```bash
./run_update_and_display.sh
```

---
## **🔄 Automating Execution**
### **📌 Wake on Event & Update via `cron`**
To set the Raspberry Pi to **wake on schedule**, update, and **display an image**, add to `cron`:

```bash
crontab -e
```
Add:
```
@reboot /bin/bash /path/to/run_update_and_display.sh
```