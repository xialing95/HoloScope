# app/epaper_display/epd_module.py
import time
import socket
import logging
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# --- Driver Import and Setup ---
# EPD_DRIVER_LOADED will be set by the import block below.
EPD_DRIVER_LOADED = False

try:
    # Attempt to import the specific hardware driver file from the same directory
    from .epd2in13b_V4 import EPD, epdconfig, GPIO 
    
    # Check if the underlying hardware access was mocked (meaning GPIO/spidev failed)
    if GPIO is not None:
        EPD_DRIVER_LOADED = True
        print("EPD driver and hardware access confirmed.")
    else:
        # Drivers failed in epd2in13b_V4.py, but the file was found.
        print("Warning: Hardware (GPIO/spidev) dependencies missing. EPD will use mock functions.")
        
    EPD_Type = EPD

except ImportError as e:
    logging.warning(f"EPD driver (epd2in13b_V4.py) or dependencies (PIL) not found: {e}")
    
    # Mocking classes allows the rest of the module to be callable without crashing
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


# --- Configuration & Setup ---
# NOTE: Update this path to where your font file is located on the system.
# Using a common system font as a robust fallback.
FONTDIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" 
SECTION_HEIGHT = 40

# --- Utility Functions ---

def get_ip_address():
    """Gets the local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Offline"
        
def get_hostname():
    """Gets the hostname."""
    try:
        return socket.gethostname()
    except Exception:
        return "Unknown Host"

# --- Drawing Functions ---
def draw_section_text(draw, font, text: str, y_pos: int):
    """Generic helper to draw text at a specific vertical position."""
    # Center the text based on standard EPD width (250)
    text_width, _ = draw.textsize(text, font=font)
    x_pos = (250 - text_width) // 2
    
    draw.text((x_pos, y_pos), text, font=font, fill=0)

# --- Initialization and Update Core Functions ---

def initialize_epd_and_fonts() -> Optional[Tuple[EPD_Type, Image.Image, Image.Image, ImageFont.FreeTypeFont]]:
    """Initializes the EPD hardware, loads fonts, and creates image buffers."""
    global EPD_DRIVER_LOADED
    
    if not EPD_DRIVER_LOADED:
        print("Initialization skipped: EPD drivers unavailable.")
        return None

    try:
        epd = EPD_Type()
        epd.init()
        epd.Clear()
        time.sleep(0.5)

        try:
            # Try to load the custom font, fall back to default
            font_section = ImageFont.truetype(FONTDIC, 16) 
        except IOError:
            logging.error(f"Font file not found at {FONTDIC}. Using default PIL font.")
            font_section = ImageFont.load_default()
            
        # Create image buffers (rotated for display layout)
        HBlackimage = Image.new('1', (epd.height, epd.width), 255) # 250x122
        HRYimage = Image.new('1', (epd.height, epd.width), 255) # 250x122
        
        return epd, HBlackimage, HRYimage, font_section
        
    except Exception as e:
        logging.error(f"Failed to initialize EPD or Fonts (Hardware/SPI issue?): {e}")
        # If initialization fails here, the hardware connection is the problem.
        EPD_DRIVER_LOADED = False
        return None

def update_sensor_display(epd_kit: Tuple, temp: float, hum: float, pres: float, gas: int):
    """Draws BME680 sensor data onto the ePaper display."""
    
    epd, HBlackimage, HRYimage, font_section = epd_kit
    
    # 1. Setup
    HBlackimage.paste(255, [0, 0, epd.height, epd.width])
    HRYimage.paste(255, [0, 0, epd.height, epd.width])
    
    drawblack = ImageDraw.Draw(HBlackimage)
    drawred = ImageDraw.Draw(HRYimage)
    
    # 2. Draw Sensor Data
    draw_section_text(drawblack, font_section, "--- BME680 DATA ---", 5)

    # Main data in Black
    draw_section_text(drawblack, font_section, f"Temp: {temp:.1f} C", SECTION_HEIGHT * 1 + 5)
    draw_section_text(drawblack, font_section, f"Hum: {hum:.1f} %", SECTION_HEIGHT * 2 + 5)
    draw_section_text(drawblack, font_section, f"Pres: {pres:.1f} hPa", SECTION_HEIGHT * 3 + 5)
    
    # Gas resistance often indicates air quality; draw in Red for emphasis
    draw_section_text(drawred, font_section, f"Air Q: {gas // 1000} kOhms", SECTION_HEIGHT * 4 + 5)
    
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