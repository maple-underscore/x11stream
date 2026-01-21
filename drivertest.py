#!/usr/bin/env python3
"""
OLED Driver Test Script
Test OLED displays with custom driver, text, and I2C interface selection

Usage:
    python3 drivertest.py
    
Configuration (edit the variables below):
    - DRIVER_NAME: sh1106, ssd1306, ssd1305, or ssd1309
    - DISPLAY_TEXT: Any text to display on the OLED
    - I2C_SDA_PIN: I2C SDA pin name (e.g., I2C2_SDA_M0, SDA, GPIO2)
    - I2C_SCL_PIN: I2C SCL pin name (e.g., I2C2_SCL_M0, SCL, GPIO3)
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

# I2C Interface Selection
# Examples for Orange Pi:
#   - I2C2_SDA_M0 and I2C2_SCL_M0
#   - I2C0_SDA and I2C0_SCL
# Examples for Raspberry Pi:
#   - GPIO2 (SDA) and GPIO3 (SCL)
#   - SDA and SCL (default)
I2C_SDA_PIN = "I2C2_SDA_M0"
I2C_SCL_PIN = "I2C2_SCL_M0"

# I2C address (most OLED displays use 0x3C or 0x3D)
I2C_ADDRESS = 0x3C

# Display dimensions (standard for these drivers)
WIDTH = 128
HEIGHT = 64

# ============================================================================
# END CONFIGURATION
# ============================================================================

def setup_board_pins():
    """Configure board library to use the specified I2C pins."""
    import board
    
    # Get the actual pin objects from the pin names
    try:
        # Try to get the pin by name (e.g., I2C2_SDA_M0)
        sda_pin = getattr(board, I2C_SDA_PIN, None)
        scl_pin = getattr(board, I2C_SCL_PIN, None)
        
        if sda_pin is None:
            print(f"Error: SDA pin '{I2C_SDA_PIN}' not found on board", file=sys.stderr)
            print("Available pins:", file=sys.stderr)
            available_pins = [p for p in dir(board) if not p.startswith('_')]
            for i in range(0, len(available_pins), 8):
                print("  " + ", ".join(available_pins[i:i+8]), file=sys.stderr)
            sys.exit(1)
        
        if scl_pin is None:
            print(f"Error: SCL pin '{I2C_SCL_PIN}' not found on board", file=sys.stderr)
            print("Available pins:", file=sys.stderr)
            available_pins = [p for p in dir(board) if not p.startswith('_')]
            for i in range(0, len(available_pins), 8):
                print("  " + ", ".join(available_pins[i:i+8]), file=sys.stderr)
            sys.exit(1)
        
        return sda_pin, scl_pin
    except AttributeError as e:
        print(f"Error accessing board pins: {e}", file=sys.stderr)
        sys.exit(1)

def init_display():
    """Initialize the OLED display with the configured driver and I2C pins."""
    print(f"OLED Driver Test")
    print(f"================")
    print(f"Driver: {DRIVER_NAME.upper()}")
    print(f"Text: '{DISPLAY_TEXT}'")
    print(f"I2C Pins: SDA={I2C_SDA_PIN}, SCL={I2C_SCL_PIN}")
    print(f"I2C Address: 0x{I2C_ADDRESS:02X}")
    print()
    
    # Import required libraries
    try:
        import busio
    except ImportError as e:
        print(f"Error: Required library not available: {e}", file=sys.stderr)
        print("Please install: pip3 install --user adafruit-blinka Pillow", file=sys.stderr)
        sys.exit(1)
    
    # Get I2C pins from board
    sda_pin, scl_pin = setup_board_pins()
    
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
        print(f"Please install: pip3 install --user adafruit-circuitpython-{DRIVER_NAME}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize I2C bus with custom pins
    print(f"Initializing I2C bus...")
    try:
        i2c = busio.I2C(scl_pin, sda_pin)
    except Exception as e:
        print(f"Error initializing I2C bus: {e}", file=sys.stderr)
        print("Please check:", file=sys.stderr)
        print("  - I2C is enabled on your system", file=sys.stderr)
        print("  - Pin names are correct for your board", file=sys.stderr)
        print("  - Display is properly connected", file=sys.stderr)
        sys.exit(1)
    
    # Initialize the display
    print(f"Initializing {DRIVER_NAME.upper()} display...")
    try:
        driver_class_name = f"{DRIVER_NAME.upper()}_I2C"
        # Check if the driver class exists
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
        print("  - I2C pins are correct", file=sys.stderr)
        print("  - Display is powered on", file=sys.stderr)
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
