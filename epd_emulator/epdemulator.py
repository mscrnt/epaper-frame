# path = epd_emulator/epdemulator.py

import json
from PIL import Image, ImageTk, ImageDraw
import tkinter as tk
from flask import Flask, render_template_string, send_file
import io
import threading
import webbrowser
import time
import os
import traceback

currentdir = os.path.dirname(os.path.realpath(__file__))

class EPD:
    def __init__(self, config_file="epd2in13", use_tkinter=False, use_color=False, update_interval=2, reverse_orientation=False): 
        config_path = os.path.join(currentdir, 'config', f'{config_file}.json')
        self.load_config(config_path)
        
        self.use_color = use_color  
        self.image_mode = 'RGB' if self.use_color else '1'  

        if reverse_orientation:
            self.width, self.height = self.height, self.width

        self.image = Image.new(self.image_mode, (self.width, self.height), "white")
        self.use_tkinter = use_tkinter
        self.update_interval = update_interval  # Keep in seconds
        print(f"✅ EPD Emulator initialized with update interval: {self.update_interval}s")

        if self.use_tkinter:
            self.init_tkinter()
        else:
            self.init_flask()
            self.start_image_update_loop()

        self.draw = ImageDraw.Draw(self.image)

    def load_config(self, config_file):
        """Load the display configuration from a JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.width = config.get('width', 122)
                self.height = config.get('height', 250)
                self.color = config.get('color', 'white')
                self.text_color = config.get('text_color', 'black')
        except Exception as e:
            print(f"❌ Error loading config file: {e}")

    def init_tkinter(self):
        """Initialize the Tkinter GUI window."""
        self.root = tk.Tk()
        self.root.title(f"Waveshare {self.width}x{self.height} EPD Emulator")
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height)
        self.canvas.pack()
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
        self.update_tkinter()

    def update_tkinter(self):
        """Update the Tkinter window."""
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.itemconfig(self.image_on_canvas, image=self.tk_image)
        self.root.update()
        self.root.after(int(self.update_interval * 1000), self.update_tkinter)

    def init_flask(self):
        """Initialize Flask web server."""
        self.app = Flask(__name__)

        @self.app.route('/')
        def index():
            """Serve the HTML page."""
            return render_template_string(f'''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>EPD Emulator</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            text-align: center;
                        }}
                        img {{
                            width: auto;
                            height: {self.height}px;
                            border: 2px solid black;
                        }}
                    </style>
                    <script>
                        function updateImage() {{
                            var image = document.getElementById("screenImage");
                            image.src = "screen.png?t=" + new Date().getTime(); // Prevent caching
                        }}
                        setInterval(updateImage, {int(self.update_interval * 1000)});
                    </script>
                </head>
                <body>
                    <h2>EPD Emulator</h2>
                    <img id="screenImage" src="screen.png" alt="EPD Emulator">
                </body>
                </html>
            ''')

        @self.app.route('/screen.png')
        def display_image():
            """Serve the latest image file."""
            try:
                screen_path = os.path.join(os.path.dirname(__file__), 'screen.png')
                if not os.path.exists(screen_path):
                    print("⚠ screen.png not found. Generating new image.")
                    self.update_image_bytes()

                response = send_file(screen_path, mimetype='image/png')
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            except Exception as e:
                traceback.print_exc()
                return "Internal Server Error", 500

        threading.Thread(target=self.run_flask).start()

    def run_flask(self):
        """Start Flask server."""
        webbrowser.open("http://127.0.0.1:5000/")
        self.app.run(port=5000, debug=False, use_reloader=False)

    def update_image_bytes(self):
        """Save the current image to disk, ensuring no conflicts."""
        try:
            screen_path = os.path.join(os.path.dirname(__file__), 'screen.png')
            backup_path = os.path.join(os.path.dirname(__file__), 'screen_old.png')

            # Delete or rename `screen.png` before saving new image
            if os.path.exists(screen_path):
                print("🗑 Removing previous screen.png to avoid conflicts.")
                os.remove(screen_path)  # Change to os.rename(screen_path, backup_path) if keeping backups

            # Save the new image
            self.image.save(screen_path, format='PNG')
            print("✅ EPD Emulator updated screen.png")
        except Exception as e:
            print(f"❌ Error updating screen.png: {e}")

    def start_image_update_loop(self):
        """Continuously update the image for Flask display."""
        def update_loop():
            while True:
                self.update_image_bytes()
                time.sleep(self.update_interval)

        threading.Thread(target=update_loop, daemon=True).start()

    def init(self):
        """Initialize the ePaper display."""
        print("✅ EPD initialized")

    def Clear(self, color):
        """Clear the screen."""
        self.image = Image.new(self.image_mode, (self.width, self.height), "white")
        self.draw = ImageDraw.Draw(self.image)  
        self.update_image_bytes()
        print("✅ Screen cleared")

    def display(self, image_buffer):
        """Display the updated image."""
        self.update_image_bytes()

    def paste_image(self, image, box=None, mask=None):
        """Paste an image onto the simulated e-paper display."""
        self.image.paste(image, box, mask)
        self.update_image_bytes()

    def sleep(self):
        """Simulate e-paper sleep mode."""
        print("💤 EPD sleep mode activated")

    def Dev_exit(self):
        """Exit the emulator."""
        print("🔴 EPD Emulator shutting down")
        if self.use_tkinter:
            self.root.destroy()
