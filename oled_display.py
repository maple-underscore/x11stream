#!/usr/bin/env python3
"""
OLED Display Management for Orange Pi
Displays local IP address and streaming status on SSD1306 OLED display
Connected via I2C (I2C_SDA_M0 and I2C_SCL_M0 pins)
"""

import time
import sys
import subprocess
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# Display dimensions
WIDTH = 128
HEIGHT = 64

# I2C address (default for SSD1306)
I2C_ADDRESS = 0x3C

def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        # Try using ip route first (same as in x11stream.sh)
        result = subprocess.run(
            ["ip", "route", "get", "1"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            for part in result.stdout.split():
                if '.' in part and part.count('.') == 3:
                    # Basic validation for IPv4
                    try:
                        octets = part.split('.')
                        if all(0 <= int(o) <= 255 for o in octets):
                            return part
                    except (ValueError, IndexError):
                        continue
        
        # Fallback to hostname -I
        result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            if ips:
                return ips[0]
    except Exception as e:
        print(f"Error getting IP address: {e}", file=sys.stderr)
    
    return "No IP"

def get_stream_status():
    """Check if the x11stream service is running."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "x11stream.service"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip() == "active":
            return "Streaming"
        else:
            return "Stopped"
    except Exception:
        # If systemctl is not available, check for ffmpeg process
        try:
            result = subprocess.run(
                ["pgrep", "-f", "ffmpeg.*x11grab"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return "Streaming"
        except Exception:
            pass
    
    return "Unknown"

def init_display():
    """Initialize the I2C connection and OLED display."""
    try:
        # Create I2C bus using board pins
        i2c = busio.I2C(SCL, SDA)
        
        # Create the SSD1306 OLED class
        # 128x64 display with I2C address
        oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=I2C_ADDRESS)
        
        # Clear display
        oled.fill(0)
        oled.show()
        
        return oled
    except Exception as e:
        print(f"Error initializing display: {e}", file=sys.stderr)
        return None

def display_info(oled, ip_address, status):
    """Display IP address and status on the OLED."""
    try:
        # Create blank image for drawing
        image = Image.new("1", (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(image)
        
        # Use default font
        font = ImageFont.load_default()
        
        # Draw header
        draw.text((0, 0), "X11 Stream", font=font, fill=255)
        draw.line((0, 10, WIDTH, 10), fill=255)
        
        # Draw IP address
        draw.text((0, 15), "IP:", font=font, fill=255)
        draw.text((0, 27), ip_address, font=font, fill=255)
        
        # Draw status
        draw.text((0, 42), "Status:", font=font, fill=255)
        draw.text((0, 54), status, font=font, fill=255)
        
        # Display image
        oled.image(image)
        oled.show()
    except Exception as e:
        print(f"Error displaying info: {e}", file=sys.stderr)

def main():
    """Main loop to update display information."""
    print("Initializing OLED display...")
    
    # Initialize display
    oled = init_display()
    if oled is None:
        print("Failed to initialize display. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    print("OLED display initialized successfully")
    print("Displaying IP address and stream status...")
    
    # Main loop
    try:
        while True:
            # Get current information
            ip_address = get_local_ip()
            status = get_stream_status()
            
            # Update display
            display_info(oled, ip_address, status)
            
            # Wait before next update (update every 5 seconds)
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\nShutting down OLED display...")
        # Clear display on exit
        oled.fill(0)
        oled.show()
        sys.exit(0)
    except Exception as e:
        print(f"Error in main loop: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
