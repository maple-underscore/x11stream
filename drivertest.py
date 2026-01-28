#!/usr/bin/env python3
"""
OLED Driver Test Script
Test OLED displays with custom driver and CP2112 USB-to-I2C bridge
Supports optional TCA9548A I2C multiplexer

Usage:
    python3 drivertest.py
    
Configuration (edit the variables below):
    - DRIVER_NAME: sh1106, ssd1306, ssd1305, or ssd1309
    - DISPLAY_TEXT: Any text to display on the OLED
    - I2C_ADDRESS: I2C address of the OLED display (usually 0x3C or 0x3D)
    - USE_MULTIPLEXER: Set to True to use TCA9548A multiplexer
    - MULTIPLEXER_ADDRESS: I2C address of TCA9548A (usually 0x70)
    - MULTIPLEXER_CHANNEL: Channel on TCA9548A where OLED is connected (0-7)
"""

import sys
import time

# ============================================================================
# CONFIGURATION - Edit these values to customize your test
# ============================================================================

# OLED Driver Selection
# Supported drivers: sh1106, ssd1306, ssd1305, ssd1309
DRIVER_NAME = "sh1106"

# Text to display on the OLED
DISPLAY_TEXT = "Hello World!"

# I2C address (most OLED displays use 0x3C or 0x3D)
I2C_ADDRESS = 0x3C

# TCA9548A Multiplexer Configuration
USE_MULTIPLEXER = False          # Set to True to use TCA9548A multiplexer
MULTIPLEXER_ADDRESS = 0x70       # I2C address of TCA9548A
MULTIPLEXER_CHANNEL = 0          # Channel on TCA9548A (0-7)

# Display dimensions (standard for these drivers)
WIDTH = 128
HEIGHT = 64

# ============================================================================
# END CONFIGURATION
# ============================================================================

def init_display():
    """Initialize the OLED display with CP2112 USB-to-I2C bridge."""
    print(f"OLED Driver Test")
    print(f"================")
    print(f"Driver: {DRIVER_NAME.upper()}")
    print(f"Text: '{DISPLAY_TEXT}'")
    print(f"I2C Address: 0x{I2C_ADDRESS:02X}")
    if USE_MULTIPLEXER:
        print(f"Multiplexer: TCA9548A at 0x{MULTIPLEXER_ADDRESS:02X}, channel {MULTIPLEXER_CHANNEL}")
    else:
        print(f"Multiplexer: Not used")
    print()
    
    # Import required libraries
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
    
    # Find and open CP2112 device
    print(f"Searching for CP2112 USB-to-I2C bridge...")
    devices = cp2112.find_devices()
    if not devices:
        print(f"Error: No CP2112 USB-to-I2C bridge devices found", file=sys.stderr)
        print("Please check:", file=sys.stderr)
        print("  - CP2112 device is connected via USB", file=sys.stderr)
        print("  - USB device permissions are correct", file=sys.stderr)
        sys.exit(1)
    
    device_path = devices[0]
    print(f"✓ Found CP2112 device: {device_path}")
    
    # Create CP2112 device instance
    try:
        i2c_device = cp2112.CP2112Device(device_path)
        i2c_device.set_smbus_config(clock_speed=100000)  # 100kHz
        print(f"✓ CP2112 device initialized")
    except Exception as e:
        print(f"Error initializing CP2112 device: {e}", file=sys.stderr)
        sys.exit(1)
    
    # If using multiplexer, set it up
    i2c = None
    if USE_MULTIPLEXER:
        try:
            import adafruit_tca9548a
            print(f"Initializing TCA9548A multiplexer...")
            
            # Create I2C bus wrapper and multiplexer
            i2c_bus = CP2112I2CBus(i2c_device)
            multiplexer = adafruit_tca9548a.TCA9548A(i2c_bus, address=MULTIPLEXER_ADDRESS)
            i2c = multiplexer[MULTIPLEXER_CHANNEL]
            print(f"✓ TCA9548A multiplexer initialized on channel {MULTIPLEXER_CHANNEL}")
        except ImportError:
            print(f"Error: TCA9548A library not available", file=sys.stderr)
            print("Please install: pip3 install adafruit-circuitpython-tca9548a", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error initializing TCA9548A multiplexer: {e}", file=sys.stderr)
            sys.exit(1)
    
    # If not using multiplexer or multiplexer setup failed, use CP2112 directly
    if i2c is None:
        i2c = CP2112I2CBus(i2c_device)
    
    # Import the driver module
    try:
        if DRIVER_NAME == "sh1106":
            import adafruit_sh1106
            driver_module = adafruit_sh1106
        elif DRIVER_NAME == "ssd1306":
            import adafruit_ssd1306
            driver_module = adafruit_ssd1306
        elif DRIVER_NAME == "ssd1305":
            import adafruit_ssd1305
            driver_module = adafruit_ssd1305
        elif DRIVER_NAME == "ssd1309":
            import adafruit_ssd1309
            driver_module = adafruit_ssd1309
        else:
            print(f"Error: Unsupported driver '{DRIVER_NAME}'", file=sys.stderr)
            print("Supported drivers: sh1106, ssd1306, ssd1305, ssd1309", file=sys.stderr)
            sys.exit(1)
    except ImportError as e:
        print(f"Error: Driver module not available: {e}", file=sys.stderr)
        print(f"Please install: pip3 install adafruit-circuitpython-{DRIVER_NAME}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize the display
    print(f"Initializing {DRIVER_NAME.upper()} display...")
    try:
        driver_class_name = f"{DRIVER_NAME.upper()}_I2C"
        if not hasattr(driver_module, driver_class_name):
            print(f"Error: Driver class '{driver_class_name}' not found in module", file=sys.stderr)
            print(f"Available classes in module: {[attr for attr in dir(driver_module) if not attr.startswith('_')]}", file=sys.stderr)
            sys.exit(1)
        
        driver_class = getattr(driver_module, driver_class_name)
        oled = driver_class(WIDTH, HEIGHT, i2c, addr=I2C_ADDRESS)
    except Exception as e:
        print(f"Error initializing display: {e}", file=sys.stderr)
        print("Please check:", file=sys.stderr)
        print(f"  - Display is connected to I2C address 0x{I2C_ADDRESS:02X}", file=sys.stderr)
        print("  - CP2112 device is working correctly", file=sys.stderr)
        print("  - Display is powered on", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"✓ Display initialized successfully")
    return oled

def display_text(oled, text):
    """Display text on the OLED screen."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create blank image for drawing
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    
    # Use default font
    font = ImageFont.load_default()
    
    # Calculate text position to center it
    # For multi-line text, split by newlines
    lines = text.split('\n')
    
    # Start from top with some padding
    y_position = 10
    
    for line in lines:
        # Draw each line
        draw.text((5, y_position), line, font=font, fill=255)
        y_position += 12  # Move down for next line
    
    # Display the image on OLED
    oled.image(image)
    oled.show()
    
    print(f"✓ Text displayed: '{text}'")

def main():
    """Main function to run the driver test."""
    try:
        # Initialize display
        oled = init_display()
        
        # Clear display first
        print("Clearing display...")
        oled.fill(0)
        oled.show()
        time.sleep(0.5)
        
        # Display the configured text
        print(f"Displaying text...")
        display_text(oled, DISPLAY_TEXT)
        
        print()
        print("✓ Test completed successfully!")
        print("The text should now be visible on your OLED display.")
        print()
        print("Press Ctrl+C to exit and clear the display.")
        
        # Keep the display on until user interrupts
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nClearing display...")
            oled.fill(0)
            oled.show()
            print("Display cleared. Exiting.")
    
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
