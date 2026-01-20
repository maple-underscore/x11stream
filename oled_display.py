#!/usr/bin/env python3
"""
OLED Display Management for Orange Pi
Displays local IP address and streaming status on SSD1306 OLED display
Connected via I2C (I2C_SDA_M0 and I2C_SCL_M0 pins)
"""

import time
import sys
import subprocess

# Import board library for I2C pin definitions
try:
    from board import SCL, SDA
    import busio
except (ImportError, NotImplementedError) as e:
    print(f"Error: CircuitPython board library not available: {e}", file=sys.stderr)
    print("Please install: sudo pip3 install adafruit-blinka", file=sys.stderr)
    sys.exit(1)

from PIL import Image, ImageDraw, ImageFont

# Import Adafruit SSD1306 library
try:
    import adafruit_ssd1306
except ImportError as e:
    print(f"Error: Adafruit SSD1306 library not available: {e}", file=sys.stderr)
    print("Please install: sudo pip3 install adafruit-circuitpython-ssd1306", file=sys.stderr)
    sys.exit(1)

# Display dimensions
WIDTH = 128
HEIGHT = 64

# I2C address (default for SSD1306)
# Most SSD1306 displays use 0x3C, but some use 0x3D
# To change: set I2C_ADDRESS environment variable or modify this value
I2C_ADDRESS = 0x3C

def get_local_ip():
    """Get the local IP address of the machine.
    
    Uses the same approach as x11stream.sh:
    1. First tries 'ip route get 1' which queries the routing table for the
       primary interface used to reach 1.0.0.0 (a public IP). This reliably
       finds the IP address of the interface with the default route.
    2. Falls back to 'hostname -I' if the first method fails.
    
    Returns:
        str: The local IP address, or "No IP" if not found.
    """
    try:
        # Try using ip route first (same as in x11stream.sh)
        # This queries which interface would be used to reach 1.0.0.0
        result = subprocess.run(
            ["ip", "route", "get", "1"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            # Match the shell script logic: awk '{print $7; exit}'
            # The 7th field contains the source IP address
            parts = result.stdout.split()
            if len(parts) >= 7:
                ip = parts[6]  # 0-indexed, so field 7 is index 6
                # Validate it's a valid IPv4 address
                try:
                    octets = ip.split('.')
                    if len(octets) == 4 and all(0 <= int(o) <= 255 for o in octets):
                        return ip
                except (ValueError, IndexError):
                    pass
        
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
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
        print(f"Error getting IP address: {e}", file=sys.stderr)
    
    return "No IP"

def get_stream_status():
    """Check if the x11stream service is running.
    
    Returns:
        str: "Streaming" if active, "Stopped" if inactive, "Unknown" if can't determine.
    """
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
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
        # Log systemctl failure before attempting fallback
        print(f"Warning: Unable to check systemctl status: {e}", file=sys.stderr)
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
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            # Failed to check ffmpeg process; fall back to reporting unknown status
            print(f"Warning: Unable to check ffmpeg streaming process: {e}", file=sys.stderr)
    
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
    
    # Cache previous values to avoid unnecessary updates
    previous_ip = None
    previous_status = None
    
    # Retry configuration for transient errors
    max_retries = 3
    retry_delay = 5  # seconds
    consecutive_errors = 0
    
    # Main loop
    try:
        while True:
            try:
                # Get current information
                ip_address = get_local_ip()
                status = get_stream_status()
                
                # Only update display when IP address or status has changed
                if ip_address != previous_ip or status != previous_status:
                    display_info(oled, ip_address, status)
                    previous_ip = ip_address
                    previous_status = status
                    # Reset error counter on successful update
                    consecutive_errors = 0
                
                # Wait before next update (update every 5 seconds)
                time.sleep(5)
                
            except Exception as e:
                # Handle transient I2C errors with retry logic
                consecutive_errors += 1
                print(f"Error in display update (attempt {consecutive_errors}/{max_retries}): {e}", file=sys.stderr)
                
                if consecutive_errors >= max_retries:
                    print(f"Maximum retry attempts ({max_retries}) reached. Exiting.", file=sys.stderr)
                    raise
                
                # Wait before retrying
                print(f"Retrying in {retry_delay} seconds...", file=sys.stderr)
                time.sleep(retry_delay)
    
    except KeyboardInterrupt:
        print("\nShutting down OLED display...")
        # Clear display on exit
        try:
            oled.fill(0)
            oled.show()
        except Exception as e:
            print(f"Error clearing display on exit: {e}", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error in main loop: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
