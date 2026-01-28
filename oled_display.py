#!/usr/bin/env python3
"""
OLED Display Management
Displays local IP address and streaming status on OLED display
Supports multiple drivers: SSD1306, SH1106, SSD1305, SSD1309
Connected via CP2112 USB-to-I2C bridge with optional TCA9548A multiplexer

Works on any system with USB support (Linux, Orange Pi, Raspberry Pi, etc.)
"""

import time
import sys
import subprocess
import glob
import os

# Import CP2112 library for USB-to-I2C communication
try:
    import cp2112
except ImportError as e:
    print(f"Error: CP2112 library not available: {e}", file=sys.stderr)
    print("Please install: pip3 install cp2112", file=sys.stderr)
    sys.exit(1)

# Import CP2112 I2C bus wrapper
try:
    from cp2112_i2c_bus import CP2112I2CBus
except ImportError as e:
    print(f"Error: CP2112 I2C bus wrapper not available: {e}", file=sys.stderr)
    print("Please ensure cp2112_i2c_bus.py is in the same directory", file=sys.stderr)
    sys.exit(1)

from PIL import Image, ImageDraw, ImageFont

# Import Adafruit OLED libraries
DRIVER_MODULES = {}
try:
    import adafruit_ssd1306
    DRIVER_MODULES['ssd1306'] = adafruit_ssd1306
except ImportError:
    pass

try:
    import adafruit_sh1106
    DRIVER_MODULES['sh1106'] = adafruit_sh1106
except ImportError:
    pass

try:
    import adafruit_ssd1305
    DRIVER_MODULES['ssd1305'] = adafruit_ssd1305
except ImportError:
    pass

try:
    import adafruit_ssd1309
    DRIVER_MODULES['ssd1309'] = adafruit_ssd1309
except ImportError:
    pass

if not DRIVER_MODULES:
    print("Error: No OLED driver libraries available", file=sys.stderr)
    print("Please install at least one of:", file=sys.stderr)
    print("  sudo pip3 install adafruit-circuitpython-ssd1306", file=sys.stderr)
    print("  sudo pip3 install adafruit-circuitpython-sh1106", file=sys.stderr)
    print("  sudo pip3 install adafruit-circuitpython-ssd1305", file=sys.stderr)
    print("  sudo pip3 install adafruit-circuitpython-ssd1309", file=sys.stderr)
    sys.exit(1)

# Display dimensions
WIDTH = 128
HEIGHT = 64

# OLED Driver Selection
# Set OLED_DRIVER environment variable to choose driver
# Supported: ssd1306, sh1106, ssd1305, ssd1309
# Default: sh1106 (as requested in requirements)
OLED_DRIVER = os.environ.get('OLED_DRIVER', 'sh1106').lower()

# I2C address (default for most OLED displays)
# Most OLED displays use 0x3C, but some use 0x3D
# To change: set I2C_ADDRESS environment variable or modify this value
I2C_ADDRESS = int(os.environ.get('I2C_ADDRESS', '0x3C'), 16)

# TCA9548A multiplexer configuration
# Set USE_MULTIPLEXER environment variable to 'true' to enable TCA9548A support
# Set MULTIPLEXER_CHANNEL to select the channel (0-7) where the OLED is connected
USE_MULTIPLEXER = os.environ.get('USE_MULTIPLEXER', 'false').lower() in ('true', '1', 'yes')
MULTIPLEXER_ADDRESS = int(os.environ.get('MULTIPLEXER_ADDRESS', '0x70'), 16)
MULTIPLEXER_CHANNEL = int(os.environ.get('MULTIPLEXER_CHANNEL', '0'))

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

def check_i2c_available():
    """Check if CP2112 USB-to-I2C bridge is available.
    
    Performs diagnostic checks:
    1. Checks for CP2112 USB devices
    2. Provides helpful error messages if CP2112 is not found
    
    Returns:
        bool: True if CP2112 appears to be available, False otherwise
    """
    print("Performing CP2112 USB-to-I2C auto-check...")
    
    # Check for CP2112 devices
    try:
        devices = cp2112.find_devices()
        if not devices:
            print("Error: No CP2112 USB-to-I2C bridge devices found", file=sys.stderr)
            print("Please check:", file=sys.stderr)
            print("  - CP2112 device is connected via USB", file=sys.stderr)
            print("  - USB device permissions are correct (may need udev rules)", file=sys.stderr)
            print("  - Device is not in use by another application", file=sys.stderr)
            return False
        
        print(f"✓ Found {len(devices)} CP2112 USB-to-I2C bridge device(s)")
        for i, device in enumerate(devices):
            print(f"  Device {i}: {device}")
        
        return True
        
    except Exception as e:
        print(f"Error checking for CP2112 devices: {e}", file=sys.stderr)
        return False

def init_display():
    """Initialize the CP2112 USB-to-I2C connection and OLED display."""
    try:
        # Validate driver selection
        if OLED_DRIVER not in DRIVER_MODULES:
            available = ', '.join(DRIVER_MODULES.keys())
            print(f"Error: Unsupported driver '{OLED_DRIVER}'", file=sys.stderr)
            print(f"Available drivers: {available}", file=sys.stderr)
            return None
        
        print(f"Initializing {OLED_DRIVER.upper()} display at I2C address 0x{I2C_ADDRESS:02X}...")
        
        # Find and open CP2112 device
        devices = cp2112.find_devices()
        if not devices:
            print("Error: No CP2112 USB-to-I2C bridge devices found", file=sys.stderr)
            return None
        
        # Use the first available CP2112 device
        device_path = devices[0]
        print(f"Using CP2112 device: {device_path}")
        
        # Create CP2112 device instance
        i2c_device = cp2112.CP2112Device(device_path)
        
        # Configure I2C speed (100kHz is standard for most OLED displays)
        i2c_device.set_smbus_config(clock_speed=100000)
        
        # If using TCA9548A multiplexer, select the appropriate channel
        i2c = None
        if USE_MULTIPLEXER:
            try:
                import adafruit_tca9548a
                print(f"Using TCA9548A multiplexer at address 0x{MULTIPLEXER_ADDRESS:02X}, channel {MULTIPLEXER_CHANNEL}")
                
                # Create I2C bus wrapper and multiplexer
                i2c_bus = CP2112I2CBus(i2c_device)
                multiplexer = adafruit_tca9548a.TCA9548A(i2c_bus, address=MULTIPLEXER_ADDRESS)
                i2c = multiplexer[MULTIPLEXER_CHANNEL]
            except ImportError:
                print("Warning: TCA9548A support requested but library not installed", file=sys.stderr)
                print("Install with: pip3 install adafruit-circuitpython-tca9548a", file=sys.stderr)
                print("Continuing without multiplexer...", file=sys.stderr)
                # Fall through to use CP2112 directly
            except Exception as e:
                print(f"Warning: Failed to initialize TCA9548A multiplexer: {e}", file=sys.stderr)
                print("Continuing without multiplexer...", file=sys.stderr)
                # Fall through to use CP2112 directly
        
        # If not using multiplexer or multiplexer setup failed, use CP2112 directly
        if i2c is None:
            i2c = CP2112I2CBus(i2c_device)
        
        # Create the OLED display class based on driver selection
        driver_module = DRIVER_MODULES[OLED_DRIVER]
        
        # Initialize the appropriate driver class
        # All drivers use the same interface: DriverName_I2C(width, height, i2c, addr)
        driver_class_name = f"{OLED_DRIVER.upper()}_I2C"
        driver_class = getattr(driver_module, driver_class_name)
        oled = driver_class(WIDTH, HEIGHT, i2c, addr=I2C_ADDRESS)
        
        # Clear display
        oled.fill(0)
        oled.show()
        
        print(f"✓ {OLED_DRIVER.upper()} display initialized successfully")
        
        return oled
    except Exception as e:
        print(f"Error initializing display: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
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
    
    # Perform I2C auto-check
    if not check_i2c_available():
        print("I2C auto-check failed. Cannot continue.", file=sys.stderr)
        sys.exit(1)
    
    print()  # Add blank line for readability
    
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
