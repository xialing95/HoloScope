# epd_module.py
import time
import socket
import subprocess
import logging
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# --- Configuration & Setup (Must be absolute paths or relative to the module) ---
# NOTE: Update this path to where your font file is located on the system.
FONTDIC = "/home/pi/HoloScope/app/epaper_display/Font.ttc" 
SECTION_HEIGHT = 40

# --- EPD Driver Loading (This logic needs to be simplified for a module) ---
try:
    # Assuming epd2in13b_V4.py is accessible in the Python path
    from epd2in13b_V4 import EPD, epdconfig
    EPD_DRIVER_LOADED = True
    EPD_Type = EPD
except ImportError as e:
    logging.warning(f"EPD driver not found. Display functions will be mocked: {e}")
    # Mocking classes allows external scripts to call these functions without crashing
    class MockEPD:
        def init(self): pass
        def Clear(self): pass
        def display(self, *args): pass
        def sleep(self): pass
        def getbuffer(self, image): return bytearray()
        height = 250
        width = 122
    EPD_Type = MockEPD
    epdconfig = type('MockConfig', (object,), {'module_exit': lambda cleanup: None})
    EPD_DRIVER_LOADED = False

# --- Utility Functions ---
# Note: Keeping network functions here is cleaner for the display logic
def get_ip_address():
    # ... (body remains the same as your original script) ...
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Offline"
        
def get_hostname():
    # ... (body remains the same as your original script) ...
    try:
        return socket.gethostname()
    except Exception:
        return "Unknown Host"

# --- Drawing Functions ---
# Only include the essential drawing functions here

def draw_section_text(draw, font, text: str, y_pos: int):
    """Generic helper to draw text at a specific vertical position."""
    draw.text((5, y_pos), text, font=font, fill=0)

# --- Initialization and Update Core Functions ---

def initialize_epd_and_fonts() -> Optional[Tuple[EPD_Type, Image.Image, Image.Image, ImageFont.FreeTypeFont]]:
    """Initializes the EPD hardware, loads fonts, and creates image buffers."""
    if not EPD_DRIVER_LOADED:
        return None

    try:
        epd = EPD_Type()
        epd.init()
        epd.Clear()
        time.sleep(0.5)

        try:
            font_section = ImageFont.truetype(FONTDIC, 16) 
        except IOError:
            logging.error(f"Font file not found at {FONTDIC}. Using default font.")
            font_section = ImageFont.load_default()
            
        HBlackimage = Image.new('1', (epd.height, epd.width), 255)
        HRYimage = Image.new('1', (epd.height, epd.width), 255)
        
        return epd, HBlackimage, HRYimage, font_section
        
    except Exception as e:
        logging.error(f"Failed to initialize EPD or Fonts: {e}")
        return None

def update_sensor_display(epd_kit: Tuple, temp: float, hum: float, pres: float, gas: int):
    """Draws BME680 sensor data onto the ePaper display."""
    
    epd, HBlackimage, HRYimage, font_section = epd_kit
    
    # 1. Setup
    HBlackimage.paste(255, [0, 0, epd.height, epd.width])
    drawblack = ImageDraw.Draw(HBlackimage)
    
    # 2. Draw Sensor Data
    draw_section_text(drawblack, font_section, f"Temp: {temp:.1f} C", 5)
    draw_section_text(drawblack, font_section, f"Hum: {hum:.1f} %", SECTION_HEIGHT * 1 + 5)
    draw_section_text(drawblack, font_section, f"Pres: {pres:.1f} hPa", SECTION_HEIGHT * 2 + 5)
    draw_section_text(drawblack, font_section, f"Gas: {gas // 1000} kOhms", SECTION_HEIGHT * 3 + 5)
    
    # 3. Display
    epd.display(epd.getbuffer(HBlackimage), epd.getbuffer(HRYimage))

def cleanup_epd(epd_kit: Tuple):
    """Puts the display to sleep and cleans up the driver module."""
    if EPD_DRIVER_LOADED:
        try:
            epd_kit[0].sleep()
            epdconfig.module_exit(cleanup=True)
            print("E-Paper display put to sleep and module cleaned up.")
        except:
            pass