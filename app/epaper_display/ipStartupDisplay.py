#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
FONTDIC = "/home/pi/Soil_monitoring_azure/Font.ttc"

import logging
import epd2in13b_V4
import time
from PIL import Image,ImageDraw,ImageFont

import socket
import subprocess

def get_ip_address():
    try:
        # Connect to an external host to force the system to use the default interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google's DNS
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return f"Error: {e}"

def get_wifi_name():
    try:
        # Uses iwgetid to get the current WiFi SSID
        result = subprocess.check_output(["iwgetid", "-r"]).decode().strip()
        return result if result else "Not connected to Wi-Fi"
    except subprocess.CalledProcessError:
        return "NA"

logging.basicConfig(level=logging.DEBUG)

try:
    ip = get_ip_address()
    ssid = get_wifi_name()
    
    epd = epd2in13b_V4.EPD()
    logging.info("init and Clear")
    epd.init()
    epd.Clear()
    time.sleep(1)
    
    # Drawing on the image
    logging.info("Drawing")    
    font20 = ImageFont.truetype(FONTDIC, 20)
    font18 = ImageFont.truetype(FONTDIC, 18)
    
    # Drawing on the Horizontal image
    logging.info("1.Drawing on the Horizontal image...") 
    HBlackimage = Image.new('1', (epd.height, epd.width), 255)  # 250*122
    HRYimage = Image.new('1', (epd.height, epd.width), 255)  # 250*122
    drawblack = ImageDraw.Draw(HBlackimage)
    drawry = ImageDraw.Draw(HRYimage)
    drawblack.text((10, 0), f"IP: {ip}", font = font20, fill = 0)
    drawblack.text((10, 20), f"Wi-Fi SSID: {ssid}", font = font20, fill = 0)
    epd.display(epd.getbuffer(HBlackimage), epd.getbuffer(HRYimage))
    time.sleep(2)
    
    # logging.info("Clear...")
    # epd.init()
    # epd.clear()
    
    logging.info("Goto Sleep...")
    epd.sleep()
        
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd2in13b_V4.epdconfig.module_exit(cleanup=True)
    exit()

