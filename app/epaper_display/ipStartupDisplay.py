#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import logging
import time
import socket
import subprocess
from datetime import datetime

# --- Configuration & Setup ---

FONTDIC = "/home/pi/HoloScope/app/epaper_display/Font.ttc"
SECTION_HEIGHT = 30  # Height allocated for each of the four sections (4 * 30 = 120, screen height is 122)

# Try to import the EPD driver
try:
    import epd2in13b_V4
    from PIL import Image, ImageDraw, ImageFont
    EPD_DRIVER_LOADED = True
except ImportError:
    logging.warning("EPD driver 'epd2in13b_V4' or PIL not found. Display functions will be skipped.")
    # Mock classes to allow code structure validation without hardware
    class MockEPD:
        def __init__(self): pass
        def init(self): pass
        def Clear(self): pass
        def display(self, *args): pass
        def sleep(self): pass
        def getbuffer(self, image): return bytearray()
        height = 250
        width = 122
    epd2in13b_V4 = type('MockEPDModule', (object,), {'EPD': MockEPD, 'epdconfig': type('MockConfig', (object,), {'module_exit': lambda cleanup: None})})
    EPD_DRIVER_LOADED = False

logging.basicConfig(level=logging.INFO)

# --- Network Utilities ---

def get_ip_address():
    """Retrieves the local machine's primary IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Offline"

def get_hostname():
    """Retrieves the local machine's hostname."""
    try:
        return socket.gethostname()
    except Exception:
        return "Unknown Host"

def get_wifi_name():
    """Retrieves the current Wi-Fi SSID using 'iwgetid'."""
    try:
        result = subprocess.check_output(["iwgetid", "-r"]).decode().strip()
        return result if result else "Not Connected"
    except subprocess.CalledProcessError:
        return "NA"

# --- Drawing Functions for Each Section ---

def draw_ip_hostname(draw, font, ip, hostname, y_pos):
    """Draws the IP Address and Hostname in the first section (Y=0)."""
    text = f"Host: {hostname}"
    draw.text((5, y_pos), text, font=font, fill=0)
    # Add IP on a new line or slightly offset if space allows, or simplify the host line
    text_ip = f"IP: {ip}"
    draw.text((5, y_pos + 15), text_ip, font=font, fill=0) # Using a slightly larger font for primary info

def draw_wifi_ssid(draw, font, ssid, y_pos):
    """Draws the Wi-Fi SSID in the second section (Y=30)."""
    text = f"SSID: {ssid}"
    draw.text((5, y_pos), text, font=font, fill=0)

def draw_static_status(draw, font, y_pos):
    """Draws a static System Status message in the third section (Y=60)."""
    text = "Status: READY"
    draw.text((5, y_pos), text, font=font, fill=0)

def draw_dynamic_message(draw, font, message, y_pos):
    """Draws a dynamic/updateable message (like time) in the fourth section (Y=90)."""
    text = f"Time: {message}"
    draw.text((5, y_pos), text, font=font, fill=0)

# --- Main Execution Logic ---

def main():
    """
    Main execution loop that orchestrates the data fetching and drawing.
    """
    if not EPD_DRIVER_LOADED:
        logging.error("Cannot run display script: EPD driver or PIL missing.")
        return

    # 1. Initialize EPD and Fonts
    try:
        epd = epd2in13b_V4.EPD()
        epd.init()
        epd.Clear()
        time.sleep(0.5)

        # Load Fonts (Using one size for simplicity in four tight sections)
        try:
            # We'll use a slightly smaller font for better fit, assuming 18pt is available
            font_section = ImageFont.truetype(FONTDIC, 16) 
        except IOError:
            logging.error(f"Font file not found at {FONTDIC}. Using default font.")
            font_section = ImageFont.load_default()
            
        # Create image buffers (250*122 for horizontal)
        HBlackimage = Image.new('1', (epd.height, epd.width), 255)
        HRYimage = Image.new('1', (epd.height, epd.width), 255)
        
    except Exception as e:
        logging.error(f"Failed to initialize EPD or Fonts: {e}")
        return

    # 2. Fetch Static Network Info (These won't change often)
    ip = get_ip_address()
    hostname = get_hostname()
    ssid = get_wifi_name()
    logging.info(f"Network Info | IP: {ip} | Host: {hostname} | SSID: {ssid}")

    # 3. Main Update Loop (Update every 10 seconds)
    try:
        # We will demonstrate 3 updates before sleeping
        for i in range(3):
            # Calculate the current dynamic content
            now_str = datetime.now().strftime("%H:%M:%S")
            
            # --- Drawing Orchestration ---
            
            # Reset (Clear) the drawing buffer before redrawing all sections
            HBlackimage.paste(255, [0, 0, epd.height, epd.width])
            drawblack = ImageDraw.Draw(HBlackimage)

            # Call each function to update its dedicated section
            draw_ip_hostname(drawblack, font_section, ip, hostname, 0)
            draw_wifi_ssid(drawblack, font_section, ssid, SECTION_HEIGHT * 1)
            draw_static_status(drawblack, font_section, SECTION_HEIGHT * 2)
            draw_dynamic_message(drawblack, font_section, now_str, SECTION_HEIGHT * 3)
            
            # Send the complete image buffer to the display
            epd.display(epd.getbuffer(HBlackimage), epd.getbuffer(HRYimage))
            logging.info(f"Display refreshed with time: {now_str}")
            time.sleep(10)

        # 4. Sleep
        logging.info("Goto Sleep...")
        epd.sleep()
        
    except Exception as e:
        logging.error(f"An error occurred during the update loop: {e}")
        
    except KeyboardInterrupt:    
        logging.info("Ctrl + C detected: Exiting and cleaning up EPD module.")
        epd2in13b_V4.epdconfig.module_exit(cleanup=True)
        sys.exit()

if __name__ == "__main__":
    main()
