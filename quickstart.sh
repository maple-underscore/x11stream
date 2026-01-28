#!/bin/bash
#
# quickstart.sh - Quick installation script for x11stream
#
# This script automates the installation and setup of x11stream including:
# - System dependencies (ffmpeg, i2c-tools, x11-utils)
# - Python dependencies for OLED display
# - Service installation and configuration
# - Optional OLED display setup
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root"
    print_info "The script will use sudo when necessary"
    exit 1
fi

# Welcome message
clear
print_header "X11Stream QuickStart Installation"
echo ""
echo "This script will install and configure x11stream on your system."
echo "It will:"
echo "  • Install system dependencies (ffmpeg, i2c-tools, x11-utils)"
echo "  • Set up Python environment for OLED display"
echo "  • Install and configure systemd services"
echo "  • Optionally configure OLED display support"
echo ""
read -p "Continue with installation? [Y/n]: " confirm
if [[ "$confirm" =~ ^[Nn]$ ]]; then
    echo "Installation cancelled."
    exit 0
fi

# Detect package manager
print_header "System Detection"
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
    PKG_UPDATE="sudo apt-get update"
    PKG_INSTALL="sudo apt-get install -y"
    print_success "Detected Debian/Ubuntu system (apt-get)"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    PKG_UPDATE="sudo dnf check-update || true"
    PKG_INSTALL="sudo dnf install -y"
    print_success "Detected Fedora/RHEL system (dnf)"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    PKG_UPDATE="sudo yum check-update || true"
    PKG_INSTALL="sudo yum install -y"
    print_success "Detected CentOS/RHEL system (yum)"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
    PKG_UPDATE="sudo pacman -Sy"
    PKG_INSTALL="sudo pacman -S --noconfirm"
    print_success "Detected Arch Linux system (pacman)"
else
    print_error "Unsupported package manager"
    print_info "Please install dependencies manually: ffmpeg, i2c-tools, x11-utils, python3-pip"
    exit 1
fi

# Update package lists
print_header "Updating Package Lists"
echo "Running: $PKG_UPDATE"
eval $PKG_UPDATE
print_success "Package lists updated"

# Install system dependencies
print_header "Installing System Dependencies"

# Check and install ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    print_info "Installing ffmpeg..."
    eval $PKG_INSTALL ffmpeg
    print_success "ffmpeg installed"
else
    print_success "ffmpeg already installed"
fi

# Check ffmpeg for x11grab support
if ffmpeg -formats 2>&1 | grep -q x11grab; then
    print_success "ffmpeg has x11grab support"
else
    print_warning "ffmpeg may not have x11grab support"
    print_info "You may need to recompile ffmpeg with: --enable-x11grab --enable-libx264"
fi

# Install x11-utils (for xdpyinfo)
print_info "Installing x11-utils..."
if [ "$PKG_MANAGER" = "apt-get" ]; then
    eval $PKG_INSTALL x11-utils
elif [ "$PKG_MANAGER" = "dnf" ] || [ "$PKG_MANAGER" = "yum" ]; then
    eval $PKG_INSTALL xorg-x11-utils
elif [ "$PKG_MANAGER" = "pacman" ]; then
    eval $PKG_INSTALL xorg-xdpyinfo
fi
print_success "x11-utils installed"

# Install Python3 and pip if not present
if ! command -v python3 &> /dev/null; then
    print_info "Installing Python 3..."
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        eval $PKG_INSTALL python3 python3-pip
    else
        eval $PKG_INSTALL python3 python3-pip
    fi
    print_success "Python 3 installed"
else
    print_success "Python 3 already installed ($(python3 --version))"
fi

# Ask about OLED display support
print_header "OLED Display Configuration"
echo ""
echo "Do you want to install OLED display support?"
echo "This is optional and only needed if you have an OLED display connected via I2C."
echo ""
read -p "Install OLED display support? [y/N]: " install_oled

if [[ "$install_oled" =~ ^[Yy]$ ]]; then
    # Ask for driver type
    echo ""
    echo "Select your OLED display driver:"
    echo "  1) SH1106  (128x64, common in 1.3\" displays) - Default"
    echo "  2) SSD1306 (128x64, common in 0.96\" displays)"
    echo "  3) SSD1305 (128x64)"
    echo "  4) SSD1309 (128x64)"
    echo "  5) Install all drivers"
    echo ""
    read -p "Select driver [1-5] (default: 1): " driver_choice
    
    case $driver_choice in
        2) OLED_DRIVER="ssd1306" ;;
        3) OLED_DRIVER="ssd1305" ;;
        4) OLED_DRIVER="ssd1309" ;;
        5) OLED_DRIVER="all" ;;
        *) OLED_DRIVER="sh1106" ;;
    esac
    
    # Ask for I2C address
    echo ""
    echo "Enter I2C address for your OLED display"
    read -p "I2C address (default: 0x3C): " i2c_addr
    [ -z "$i2c_addr" ] && i2c_addr="0x3C"
    
    # Ask about TCA9548A multiplexer
    echo ""
    echo "Do you want to use a TCA9548A I2C multiplexer?"
    echo "This is optional and only needed if you have multiple I2C devices."
    read -p "Use TCA9548A multiplexer? [y/N]: " use_mux
    
    if [[ "$use_mux" =~ ^[Yy]$ ]]; then
        USE_MULTIPLEXER="true"
        
        read -p "TCA9548A I2C address (default: 0x70): " mux_addr
        [ -z "$mux_addr" ] && mux_addr="0x70"
        
        read -p "TCA9548A channel (0-7, default: 0): " mux_channel
        [ -z "$mux_channel" ] && mux_channel="0"
    else
        USE_MULTIPLEXER="false"
        mux_addr="0x70"
        mux_channel="0"
    fi
    
    # Install Python dependencies
    print_info "Installing Python dependencies for OLED display..."
    
    # Install CP2112 and base dependencies
    pip3 install --user cp2112 Pillow
    
    # Install driver-specific libraries
    if [ "$OLED_DRIVER" = "all" ]; then
        print_info "Installing all OLED drivers..."
        pip3 install --user adafruit-circuitpython-ssd1306 \
                            adafruit-circuitpython-sh1106 \
                            adafruit-circuitpython-ssd1305 \
                            adafruit-circuitpython-ssd1309
    else
        print_info "Installing $OLED_DRIVER driver..."
        pip3 install --user adafruit-circuitpython-$OLED_DRIVER
    fi
    
    # Install TCA9548A library if needed
    if [[ "$use_mux" =~ ^[Yy]$ ]]; then
        print_info "Installing TCA9548A multiplexer library..."
        pip3 install --user adafruit-circuitpython-tca9548a
    fi
    
    print_success "Python dependencies installed"
    
    # Check for CP2112 USB device
    print_info "Checking for CP2112 USB-to-I2C bridge..."
    if lsusb 2>/dev/null | grep -q "10c4:ea90"; then
        print_success "CP2112 USB-to-I2C bridge detected"
        
        # Set up udev rules for non-root access
        print_info "Setting up udev rules for CP2112 device access..."
        sudo tee /etc/udev/rules.d/99-cp2112.rules > /dev/null << 'UDEV_EOF'
# CP2112 HID USB-to-SMBus Bridge
# Add user to plugdev group for access: sudo usermod -a -G plugdev $USER
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea90", GROUP="plugdev", MODE="0660"
UDEV_EOF
        
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        
        # Add user to plugdev group
        if ! groups $USER | grep -q plugdev; then
            print_info "Adding $USER to plugdev group..."
            sudo usermod -a -G plugdev $USER
            print_warning "You will need to log out and back in for group membership to take effect"
        fi
        
        print_success "udev rules configured"
    else
        print_warning "CP2112 USB-to-I2C bridge not detected"
        print_info "Please ensure:"
        print_info "  - CP2112 device is connected via USB"
        print_info "  - The device is properly recognized by the system"
        print_info "You can check with: lsusb | grep '10c4:ea90'"
    fi
    
    ENABLE_OLED=true
else
    ENABLE_OLED=false
    print_info "Skipping OLED display setup"
fi

# Install x11stream script
print_header "Installing X11Stream"
print_info "Copying x11stream.sh to /usr/local/bin/..."
sudo cp x11stream.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/x11stream.sh
print_success "x11stream.sh installed"

# Install x11stream wrapper script
if [ -f "x11stream-wrapper.sh" ]; then
    print_info "Copying x11stream-wrapper.sh to /usr/local/bin/..."
    sudo cp x11stream-wrapper.sh /usr/local/bin/
    sudo chmod +x /usr/local/bin/x11stream-wrapper.sh
    print_success "x11stream-wrapper.sh installed"
fi

# Install systemd service for x11stream
print_info "Installing x11stream systemd service..."
sudo cp x11stream.service /etc/systemd/system/
sudo systemctl daemon-reload
print_success "x11stream service installed"

# Install OLED display if enabled
if [ "$ENABLE_OLED" = true ]; then
    print_info "Installing OLED display scripts..."
    sudo cp oled_display.py /usr/local/bin/
    sudo cp cp2112_i2c_bus.py /usr/local/bin/
    sudo chmod +x /usr/local/bin/oled_display.py
    sudo chmod +x /usr/local/bin/cp2112_i2c_bus.py
    print_success "OLED display scripts installed"
    
    # Create environment file for OLED service with driver, address, and multiplexer settings
    print_info "Configuring OLED display service..."
    sudo mkdir -p /etc/default
    sudo bash -c "cat > /etc/default/oled_display << 'EOF'
# OLED Display Configuration
OLED_DRIVER=$OLED_DRIVER
I2C_ADDRESS=$i2c_addr
# TCA9548A Multiplexer Configuration
USE_MULTIPLEXER=$USE_MULTIPLEXER
MULTIPLEXER_ADDRESS=$mux_addr
MULTIPLEXER_CHANNEL=$mux_channel
EOF"
    
    # Copy and update service file to use environment file
    sudo cp oled_display.service /etc/systemd/system/oled_display.service
    
    # Insert EnvironmentFile line after [Service] section if not already present
    if ! sudo grep -q "EnvironmentFile" /etc/systemd/system/oled_display.service; then
        sudo sed -i '/^\[Service\]/a EnvironmentFile=-/etc/default/oled_display' /etc/systemd/system/oled_display.service
    fi
    
    sudo systemctl daemon-reload
    print_success "OLED display service installed"
fi

# Ask if user wants to enable and start services
print_header "Service Configuration"
echo ""
echo "Do you want to enable services to start on boot?"
read -p "Enable x11stream service? [Y/n]: " enable_x11stream
if [[ ! "$enable_x11stream" =~ ^[Nn]$ ]]; then
    sudo systemctl enable x11stream.service
    print_success "x11stream service enabled"
    
    read -p "Start x11stream service now? [y/N]: " start_x11stream
    if [[ "$start_x11stream" =~ ^[Yy]$ ]]; then
        sudo systemctl start x11stream.service
        print_success "x11stream service started"
        
        # Get IP address
        IP_ADDRESS=$(ip route get 1 2>/dev/null | awk '{print $7; exit}' || hostname -I | awk '{print $1}')
        echo ""
        print_info "Stream is available at:"
        echo "  http://${IP_ADDRESS}:8080/stream.m3u8"
        echo "  http://localhost:8080/stream.m3u8"
    fi
fi

if [ "$ENABLE_OLED" = true ]; then
    echo ""
    read -p "Enable OLED display service? [Y/n]: " enable_oled_service
    if [[ ! "$enable_oled_service" =~ ^[Nn]$ ]]; then
        sudo systemctl enable oled_display.service
        print_success "OLED display service enabled"
        
        read -p "Start OLED display service now? [y/N]: " start_oled_service
        if [[ "$start_oled_service" =~ ^[Yy]$ ]]; then
            sudo systemctl start oled_display.service
            print_success "OLED display service started"
        fi
    fi
fi

# Installation complete
print_header "Installation Complete!"
echo ""
echo "Installation summary:"
echo "  • x11stream script: /usr/local/bin/x11stream.sh"
echo "  • x11stream service: /etc/systemd/system/x11stream.service"
if [ "$ENABLE_OLED" = true ]; then
    echo "  • OLED display script: /usr/local/bin/oled_display.py"
    echo "  • OLED display service: /etc/systemd/system/oled_display.service"
    echo "  • OLED configuration: /etc/default/oled_display"
    echo "  • OLED driver: $OLED_DRIVER"
    echo "  • I2C address: $i2c_addr"
fi
echo ""
echo "Useful commands:"
echo "  • Run x11stream interactively: /usr/local/bin/x11stream.sh --interactive"
echo "  • Check service status: sudo systemctl status x11stream.service"
if [ "$ENABLE_OLED" = true ]; then
    echo "  • Check OLED status: sudo systemctl status oled_display.service"
fi
echo "  • View logs: sudo journalctl -u x11stream.service -f"
echo ""
print_success "Setup complete! Enjoy streaming with x11stream."
