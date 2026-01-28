# x11stream

Shell script on Ubuntu to auto-stream X11 display on boot using x11grab and ffmpeg with HLS (HTTP Live Streaming).

## Features

- Captures X11 display using ffmpeg with ultra-low-latency settings (400-600ms)
- **HLS streaming** for multiple concurrent connections without crashes
- **Hardware acceleration support** for Rockchip RK3588 (rkmpp), VAAPI, and Intel QSV
- Hosts an HTTP server for direct browser/VLC/mobile access
- Auto-starts on boot via systemd service with automatic restart on failures
- **Interactive mode** for easy configuration
- **Audio streaming support** with multiple quality presets
- **Auto-detect resolution** with intelligent scaling (scales down if display is larger than target)
- Configurable resolution, framerate, bitrate, and audio settings
- Bandwidth estimation for all configurations
- **OLED display support** for Orange Pi and Raspberry Pi (SH1106, SSD1306, SSD1305, SSD1309)
- **Multi-driver support** - works with common I2C OLED displays

## Key Improvements

- **No crash on client disconnect**: HLS streaming supports multiple clients and continues running when clients disconnect
- **Ultra-low latency**: Optimized to 400-600ms latency (down from 3-4 seconds)
- **Hardware acceleration**: Automatic detection and use of Rockchip MPP, VAAPI, or QSV when available
- **Better quality**: Improved encoding settings reduce compression artifacts
- **Stable streaming**: DTS discontinuity issues resolved with proper frame timing
- **Auto-restart**: Systemd service automatically restarts on any failures

## Requirements

- Ubuntu (or other Linux with X11)
- ffmpeg with x11grab support
- PulseAudio or ALSA (for audio streaming)
- systemd (for auto-start on boot)

## Quick Installation

The easiest way to get started is using the quickstart script:

```bash
git clone https://github.com/maple-underscore/x11stream.git
cd x11stream
./quickstart.sh
```

The quickstart script will:
- Install all required dependencies (ffmpeg, i2c-tools, x11-utils, Python packages)
- Set up OLED display support with your choice of driver (optional)
- Install and configure systemd services
- Guide you through the setup process interactively

### Manual Installation

If you prefer to install manually or the quickstart script doesn't work for your system:

Install ffmpeg:
```bash
sudo apt update
sudo apt install ffmpeg
```

Install x11-utils:
```bash
sudo apt-get install x11-utils
```

> [!NOTE]
> Configure ffmpeg to use x11grab and libx264:
> ```bash
> sudo ./configure --enable-x11grab --enable-libx264
> ```

## Installation

### Quick Installation (Recommended)

Use the automated quickstart script:

```bash
git clone https://github.com/maple-underscore/x11stream.git
cd x11stream
./quickstart.sh
```

The script will guide you through the installation process and configure everything automatically.

### Manual Installation

1. Clone this repository:
```bash
git clone https://github.com/maple-underscore/x11stream.git
cd x11stream
```

2. Install the script:
```bash
sudo cp x11stream.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/x11stream.sh
```

3. Install and enable the systemd service:
```bash
sudo cp x11stream.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable x11stream.service
sudo systemctl start x11stream.service
```

## Usage

### Interactive Mode
Run in interactive mode to configure all settings through a menu:
```bash
./x11stream.sh --interactive
# or
./x11stream.sh -i
```

### Non-Interactive Mode
```bash
./x11stream.sh
```

### Access the Stream

Once the script is running, access the stream via:

- **Browser**: `http://<your-ip>:8080/stream.m3u8`
- **VLC**: Open Network Stream → `http://<your-ip>:8080/stream.m3u8`
- **Mobile**: Most modern browsers and video players support HLS streams

### Service Management
```bash
# Start the service
sudo systemctl start x11stream.service

# Stop the service
sudo systemctl stop x11stream.service

# Check status
sudo systemctl status x11stream.service

# View logs
sudo journalctl -u x11stream.service -f
```

## OLED Display Support (Orange Pi / Raspberry Pi)

The x11stream project supports displaying the local IP address and streaming status on I2C OLED displays with multiple driver options. The display connects via CP2112 USB-to-I2C bridge with optional TCA9548A multiplexer support.

### Supported OLED Drivers

- **SH1106** - 128x64, common in 1.3" displays (default)
- **SSD1306** - 128x64, common in 0.96" displays
- **SSD1305** - 128x64
- **SSD1309** - 128x64

### Hardware Requirements

- Any system with USB port (Linux, Orange Pi, Raspberry Pi, etc.)
- **CP2112 USB-to-I2C Bridge** - Silicon Labs USB to I2C/SMBus bridge
- 0.96" - 1.3" OLED Display Module (128x64 pixels, I2C)
- **Optional**: TCA9548A I2C Multiplexer (if you need to connect multiple I2C devices)
- I2C connection from CP2112 to OLED:
  - SDA (Data)
  - SCL (Clock)
  - VCC (3.3V-5V)
  - GND

### OLED Display Installation

#### Quick Installation (Recommended)

The easiest way is to use the quickstart script which will guide you through driver selection:

```bash
./quickstart.sh
```

When prompted, choose to install OLED support and select your driver type.

#### Manual Installation

1. **Connect CP2112 USB-to-I2C Bridge**:
```bash
# Connect CP2112 to your system via USB
# The device should appear as a HID device (no driver installation needed on Linux)

# Verify CP2112 device is detected
lsusb | grep "10c4:ea90"  # Should show Silicon Labs CP2112 HID SMBus Bridge

# Set up udev rules for non-root access (optional but recommended)
sudo tee /etc/udev/rules.d/99-cp2112.rules << EOF
# CP2112 HID USB-to-SMBus Bridge
# Add user to plugdev group for access: sudo usermod -a -G plugdev \$USER
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea90", GROUP="plugdev", MODE="0660"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger

# Add your user to the plugdev group (replace $USER with your username if needed)
sudo usermod -a -G plugdev $USER
# Note: You'll need to log out and back in for group membership to take effect
```

2. **Connect hardware**:
```bash
# Wire the OLED display to CP2112:
# - OLED VCC to 3.3V or 5V (depending on your OLED)
# - OLED GND to GND
# - OLED SDA to CP2112 SDA
# - OLED SCL to CP2112 SCL

# If using TCA9548A multiplexer:
# - TCA9548A VCC to 3.3V or 5V
# - TCA9548A GND to GND
# - TCA9548A SDA to CP2112 SDA
# - TCA9548A SCL to CP2112 SCL
# - OLED SDA to one of TCA9548A SD0-SD7
# - OLED SCL to corresponding TCA9548A SC0-SC7
```

3. **Install Python dependencies**:

> [!TIP]
> **Recommended installation method**: Install to user directory to avoid system package conflicts.

```bash
cd x11stream

# Install CP2112 and base dependencies
pip3 install --user cp2112 Pillow

# Install driver for your display (choose one or install all):
pip3 install --user adafruit-circuitpython-sh1106   # For SH1106 (default)
pip3 install --user adafruit-circuitpython-ssd1306  # For SSD1306
pip3 install --user adafruit-circuitpython-ssd1305  # For SSD1305
pip3 install --user adafruit-circuitpython-ssd1309  # For SSD1309

# Optional: Install TCA9548A multiplexer support
pip3 install --user adafruit-circuitpython-tca9548a

# Or install all dependencies at once:
pip3 install --user -r requirements.txt
```

4. **Configure OLED driver and multiplexer** (optional):

Set the driver type, I2C address, and multiplexer settings via environment variables:

```bash
# Create environment file
sudo mkdir -p /etc/default
sudo bash -c 'cat > /etc/default/oled_display << EOF
OLED_DRIVER=sh1106
I2C_ADDRESS=0x3C
# Optional: Enable TCA9548A multiplexer
USE_MULTIPLEXER=false
MULTIPLEXER_ADDRESS=0x70
MULTIPLEXER_CHANNEL=0
EOF'
```

Available drivers: `sh1106` (default), `ssd1306`, `ssd1305`, `ssd1309`

5. **Install OLED display scripts**:
```bash
sudo cp oled_display.py /usr/local/bin/
sudo cp cp2112_i2c_bus.py /usr/local/bin/
sudo chmod +x /usr/local/bin/oled_display.py
sudo chmod +x /usr/local/bin/cp2112_i2c_bus.py
```

6. **Install and enable the OLED display service**:
```bash
sudo cp oled_display.service /etc/systemd/system/oled_display.service

# If you created an environment file, update the service to use it:
if ! sudo grep -q "EnvironmentFile" /etc/systemd/system/oled_display.service; then
    sudo sed -i '/^\[Service\]/a EnvironmentFile=-/etc/default/oled_display' /etc/systemd/system/oled_display.service
fi

sudo systemctl daemon-reload
sudo systemctl enable oled_display.service
sudo systemctl start oled_display.service
```

### OLED Display Service Management
```bash
# Start the OLED display service
sudo systemctl start oled_display.service

# Stop the OLED display service
sudo systemctl stop oled_display.service

# Check status
sudo systemctl status oled_display.service

# View logs
sudo journalctl -u oled_display.service -f
```

### OLED Display Information

The OLED display shows:
- **Header**: "X11 Stream"
- **IP Address**: Current local IP address (updates every 5 seconds)
- **Status**: Streaming status ("Streaming", "Stopped", or "Unknown")

### CP2112 USB-to-I2C Auto-Check Feature

> [!NOTE]
> The script automatically performs CP2112 USB-to-I2C diagnostics on startup:
> - **Checks for CP2112 USB devices**: Verifies CP2112 bridge is connected and accessible
> - **Initializes USB-to-I2C bridge**: Configures the CP2112 for I2C communication
> - **Supports TCA9548A multiplexer**: Optionally uses I2C multiplexer for multiple devices
> - **Provides helpful errors**: Clear guidance if CP2112 is not found or configured
> - **Supports multiple drivers**: Auto-detects and uses the configured driver
>
> Example auto-check output:
> ```
> Performing CP2112 USB-to-I2C auto-check...
> ✓ Found 1 CP2112 USB-to-I2C bridge device(s)
>   Device 0: /dev/hidraw0
> Initializing SH1106 display at I2C address 0x3C...
> Using CP2112 device: /dev/hidraw0
> ✓ SH1106 display initialized successfully
> ```

### Driver Configuration

You can configure the OLED driver and multiplexer in several ways:

1. **Environment variable** (recommended for systemd):
```bash
export OLED_DRIVER=sh1106         # or ssd1306, ssd1305, ssd1309
export I2C_ADDRESS=0x3C           # or 0x3D
export USE_MULTIPLEXER=false      # Set to true to enable TCA9548A
export MULTIPLEXER_ADDRESS=0x70   # TCA9548A address (usually 0x70)
export MULTIPLEXER_CHANNEL=0      # Channel 0-7 on TCA9548A
```

2. **System-wide configuration file**:
```bash
# Create /etc/default/oled_display
OLED_DRIVER=sh1106
I2C_ADDRESS=0x3C
USE_MULTIPLEXER=false
MULTIPLEXER_ADDRESS=0x70
MULTIPLEXER_CHANNEL=0
```

3. **Edit the Python script directly** (not recommended):
Edit `/usr/local/bin/oled_display.py` and change the default values.

### Troubleshooting OLED Display

**Display not working:**

> [!TIP]
> Troubleshooting checklist:
> - Verify CP2112 is connected: `lsusb | grep "10c4:ea90"`
> - Check USB device permissions (may need udev rules for non-root access)
> - Verify wiring connections (SDA, SCL, VCC, GND)
> - Check service logs: `sudo journalctl -u oled_display.service -f`
> - Verify correct driver is selected (check logs for driver name)
> - Try different driver if display shows garbled output
> - If using TCA9548A, verify multiplexer address and channel settings

**Wrong driver selected:**

> [!TIP]
> If the display shows garbled output or doesn't work:
> - Check which driver your display uses (consult display documentation)
> - Common 0.96" displays use SSD1306
> - Common 1.3" displays use SH1106
> - Update driver: `sudo nano /etc/default/oled_display` and change `OLED_DRIVER`
> - Restart service: `sudo systemctl restart oled_display.service`

**CP2112 USB device not found:**

> [!IMPORTANT]
> The script uses CP2112 USB-to-I2C bridge for I2C communication. The CP2112 device should be automatically detected when connected via USB.
>
> - If CP2112 is not detected, check USB connection and permissions
> - You may need to set up udev rules for non-root access to the HID device
> - If using TCA9548A multiplexer, ensure the multiplexer address and channel are configured correctly
> - The multiplexer allows you to connect multiple I2C devices with the same address

## Maintenance and Testing

### Updating the Repository

The `update.sh` script allows you to easily update your x11stream installation to the latest version:

```bash
./update.sh
```

The update script will:
- Check for uncommitted changes and offer to stash them
- Fetch the latest changes from the remote repository
- Pull and merge updates to your current branch
- Notify you if `requirements.txt` or service files were updated
- Provide instructions for updating dependencies or reloading services if needed

### Testing OLED Drivers

The `drivertest.py` script allows you to test OLED displays with CP2112 USB-to-I2C bridge and optional TCA9548A multiplexer without modifying the main display service.

#### Configuration

Edit the configuration section at the top of `drivertest.py`:

```python
# OLED Driver Selection
DRIVER_NAME = "sh1106"  # sh1106, ssd1306, ssd1305, or ssd1309

# Text to display
DISPLAY_TEXT = "Hello World!"

# I2C Address
I2C_ADDRESS = 0x3C  # Most displays use 0x3C or 0x3D

# TCA9548A Multiplexer Configuration
USE_MULTIPLEXER = False          # Set to True to use TCA9548A multiplexer
MULTIPLEXER_ADDRESS = 0x70       # I2C address of TCA9548A
MULTIPLEXER_CHANNEL = 0          # Channel on TCA9548A (0-7)
```

#### Usage

```bash
# Run the driver test
python3 drivertest.py
```

The script will:
- Display configuration information (driver, text, multiplexer settings)
- Detect and connect to CP2112 USB-to-I2C bridge
- Initialize TCA9548A multiplexer if enabled
- Initialize the selected OLED driver
- Clear the display
- Show your custom text
- Keep the display on until you press Ctrl+C

#### Use Cases

- **Test different drivers**: Quickly test which driver works with your display
- **Test CP2112 connection**: Verify USB-to-I2C bridge is working
- **Test multiplexer**: Verify TCA9548A multiplexer configuration
- **Custom messages**: Display any text on your OLED for testing
- **Troubleshooting**: Isolate display issues from the main service

#### Example Configurations

**Standard setup with SH1106 display:**
```python
DRIVER_NAME = "sh1106"
I2C_ADDRESS = 0x3C
USE_MULTIPLEXER = False
```

**With TCA9548A multiplexer on channel 2:**
```python
DRIVER_NAME = "ssd1306"
I2C_ADDRESS = 0x3C
USE_MULTIPLEXER = True
MULTIPLEXER_ADDRESS = 0x70
MULTIPLEXER_CHANNEL = 2
```

**Multiple displays on different channels:**
```python
# For display on channel 0
DRIVER_NAME = "ssd1306"
I2C_ADDRESS = 0x3C
USE_MULTIPLEXER = True
MULTIPLEXER_CHANNEL = 0

# For display on channel 1 (edit and run again)
# MULTIPLEXER_CHANNEL = 1
```

## Configuration

### Environment Variables

The following environment variables can be set to customize the stream:

| Variable            | Default      | Description                                        |
|---------------------|--------------|---------------------------------------------------|
| DISPLAY             | :0.0         | X11 display to capture                            |
| RESOLUTION          | 1920x1080    | Target resolution (auto-detects and adjusts)      |
| FRAMERATE           | 60           | Frames per second                                 |
| BITRATE             | 6M           | Video bitrate                                     |
| HTTP_PORT           | 8080         | HTTP server port                                  |
| HTTP_BIND           | 0.0.0.0      | HTTP server bind address (0.0.0.0 or 127.0.0.1)   |
| USE_HARDWARE_ACCEL  | auto         | Hardware acceleration (auto, rkmpp, vaapi, qsv, none) |
| HLS_TIME            | 1            | HLS segment duration in seconds                   |
| HLS_LIST_SIZE       | 3            | Number of segments to keep in playlist            |
| AUDIO_ENABLED       | false        | Enable audio streaming                            |
| AUDIO_BITRATE       | 128          | Audio bitrate (kbps)                              |
| AUDIO_CODEC         | aac          | Audio codec (aac, mp3, pcm)                       |
| AUDIO_SAMPLE_RATE   | 44100        | Sample rate for PCM audio                         |
| AUDIO_BIT_DEPTH     | 16           | Bit depth for PCM audio                           |

### Hardware Acceleration

The script automatically detects available hardware acceleration:
- **Rockchip RK3588/MPP**: Best for Orange Pi 5/5 Plus - uses `h264_rkmpp` encoder
- **VAAPI**: For AMD and Intel GPUs on Linux - uses `h264_vaapi` encoder
- **Intel QSV**: For Intel CPUs with Quick Sync - uses `h264_qsv` encoder
- **Software**: Falls back to `libx264` if no hardware acceleration is available

To force a specific encoder:
```bash
export USE_HARDWARE_ACCEL=rkmpp  # or vaapi, qsv, none
```

### Security Considerations

The HTTP server binds to `0.0.0.0` by default, making the stream accessible from all network interfaces. For enhanced security:

```bash
# Restrict to localhost only
export HTTP_BIND=127.0.0.1

# Or restrict to specific interface
export HTTP_BIND=192.168.1.100
```

For production use with sensitive data, consider:
- Using a reverse proxy (nginx) with authentication
- Setting up a VPN for remote access
- Using firewall rules to restrict access

### Resolution Auto-Detection

> [!NOTE]
> The script automatically detects your display resolution using `xdpyinfo`:
> - If detected resolution is **higher** than the target: captures full screen and scales down to target
> - If detected resolution is **lower** than the target: uses the native (lower) resolution
> - If resolution cannot be detected: uses the configured target resolution

### Audio Quality Presets

When using interactive mode, you can choose from these audio presets:

#### Lossy Compression (AAC/MP3)
| Preset | Bitrate   | Quality         | Bandwidth     |
|--------|-----------|-----------------|---------------|
| 1      | 64 kbps   | Voice/Low       | ~8 KB/s       |
| 2      | 128 kbps  | Standard        | ~16 KB/s      |
| 3      | 192 kbps  | Good            | ~24 KB/s      |
| 4      | 256 kbps  | High            | ~32 KB/s      |
| 5      | 320 kbps  | Maximum         | ~40 KB/s      |

#### Lossless PCM (16-bit)
| Preset | Sample Rate | Quality       | Bandwidth     |
|--------|-------------|---------------|---------------|
| 6      | 44.1 kHz    | CD quality    | ~172 KB/s     |
| 7      | 48 kHz      | DVD quality   | ~188 KB/s     |
| 8      | 96 kHz      | Hi-Res        | ~375 KB/s     |
| 9      | 192 kHz     | Ultra Hi-Res  | ~750 KB/s     |

#### Lossless PCM (24-bit)
| Preset | Sample Rate | Quality            | Bandwidth     |
|--------|-------------|--------------------|---------------|
| 10     | 44.1 kHz    | Studio             | ~258 KB/s     |
| 11     | 48 kHz      | Professional       | ~281 KB/s     |
| 12     | 96 kHz      | Hi-Res Studio      | ~563 KB/s     |
| 13     | 192 kHz     | Ultra Hi-Res Studio| ~1125 KB/s    |

### Video Quality Presets

| Bitrate | Quality           | Bandwidth     |
|---------|-------------------|---------------|
| 2M      | Low bandwidth     | ~250 KB/s     |
| 4M      | Medium quality    | ~500 KB/s     |
| 6M      | Good quality      | ~750 KB/s     |
| 10M     | High quality      | ~1.25 MB/s    |
| 15M     | Very high         | ~1.9 MB/s     |
| 20M     | Excellent         | ~2.5 MB/s     |

To modify these settings permanently, edit the service file:
```bash
sudo systemctl edit x11stream.service
```

Or edit `/etc/systemd/system/x11stream.service` directly.

## Troubleshooting

### "Display not found" error

> [!WARNING]
> Ensure X11 is running and the `DISPLAY` variable is set correctly. On systems with multiple displays, try `:1.0` or `:0.1`.

### "Permission denied" error

> [!WARNING]
> The user running the script needs access to the X11 display. Run with appropriate permissions or add the user to the video group.

### Stream not accessible

> [!TIP]
> Common solutions:
> - Check if ffmpeg is running: `ps aux | grep ffmpeg`
> - Ensure the port is not blocked by firewall: `sudo ufw allow 8080/tcp`
> - Verify the IP address and port in the startup output

### Audio not working

> [!TIP]
> Troubleshooting steps:
> - Ensure PulseAudio or ALSA is running
> - Check audio source: `pactl list short sources` (PulseAudio)
> - Try different audio source in interactive mode

## License

MIT License
