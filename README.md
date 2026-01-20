# x11stream

Shell script on Ubuntu to auto-stream X11 display on boot using x11grab and ffmpeg.

## Features

- Captures X11 display using ffmpeg with low-latency settings
- Hosts an HTTP server for direct browser/VLC access
- Auto-starts on boot via systemd service
- **Interactive mode** for easy configuration
- **Audio streaming support** with multiple quality presets
- **Auto-detect resolution** with intelligent scaling (scales down if display is larger than target)
- Configurable resolution, framerate, bitrate, and audio settings
- Bandwidth estimation for all configurations
- **OLED display support** for Orange Pi (SSD1306, 128x64, I2C)

## Requirements

- Ubuntu (or other Linux with X11)
- ffmpeg with x11grab support
- PulseAudio or ALSA (for audio streaming)
- systemd (for auto-start on boot)

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

- **Browser**: `http://<your-ip>:8080/stream`
- **VLC**: Open Network Stream → `http://<your-ip>:8080/stream`

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

## OLED Display Support (Orange Pi)

The x11stream project supports displaying the local IP address and streaming status on a 0.96" SSD1306 OLED display connected via I2C.

### Hardware Requirements

- Orange Pi (tested on Orange Pi 5)
- 0.96" OLED Display Module (SSD1306, 128x64 pixels, I2C)
- I2C connection using pins:
  - `I2C_SDA_M0` (SDA/Data)
  - `I2C_SCL_M0` (SCL/Clock)
  - VCC (3.3V-5V)
  - GND

### OLED Display Installation

1. **Enable I2C on Orange Pi**:
```bash
# Install I2C tools and Python package manager
sudo apt-get install -y i2c-tools python3-pip

# Enable I2C using armbian-config (recommended method for Armbian-based systems)
sudo armbian-config
# Navigate to: System -> Hardware -> enable i2c0 or i2c1
# Save and reboot

# Alternative: For manual configuration, you can edit /boot/orangepiEnv.txt
# Add or uncomment the following line:
# overlays=i2c0
# Then reboot the system
```

2. **Verify I2C connection**:
```bash
# Check if I2C device is detected (default address: 0x3C)
sudo i2cdetect -y 0  # Try bus 0
# or
sudo i2cdetect -y 1  # Try bus 1
```

3. **Install Python dependencies**:

> [!TIP]
> **Recommended installation method**: Install to user directory to avoid system package conflicts.

```bash
cd x11stream
# Option 1: Install to user directory (recommended)
pip3 install --user -r requirements.txt

# Option 2: Install system-wide (requires sudo, may conflict with system packages)
# sudo pip3 install -r requirements.txt

# Option 3: Use a virtual environment (best practice for development)
# python3 -m venv .venv
# source .venv/bin/activate
# pip install -r requirements.txt
```

4. **Install OLED display script**:
```bash
sudo cp oled_display.py /usr/local/bin/
sudo chmod +x /usr/local/bin/oled_display.py
```

5. **Install and enable the OLED display service**:
```bash
sudo cp oled_display.service /etc/systemd/system/
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

### I2C Auto-Check Feature

> [!NOTE]
> The script automatically performs I2C diagnostics on startup:
> - **Checks for I2C device nodes**: Verifies `/dev/i2c-*` devices exist
> - **Scans I2C buses**: Uses `i2cdetect` to find SSD1306 display at 0x3C or 0x3D
> - **Provides helpful errors**: Clear guidance if I2C is not configured
>
> Example auto-check output:
> ```
> Performing I2C auto-check...
> ✓ Found I2C device nodes: /dev/i2c-0, /dev/i2c-1
> ✓ I2C device detected on bus 0 at address 0x3C or 0x3D
> ```

### Troubleshooting OLED Display

**Display not working:**

> [!TIP]
> Troubleshooting checklist:
> - Verify I2C is enabled: `sudo i2cdetect -y 0` or `sudo i2cdetect -y 1`
> - Check if device appears at address 0x3C
> - Verify wiring connections (SDA, SCL, VCC, GND)
> - Check service logs: `sudo journalctl -u oled_display.service -f`

**Wrong I2C bus:**

> [!IMPORTANT]
> The script uses `board.SCL` and `board.SDA`, which are the default I2C pins defined by the board library. They do not auto-detect alternate buses or pins.
>
> - If you're using a different I2C bus, you may need to modify the Python script
> - For manual configuration, check which I2C bus your display is on with `i2cdetect`
> - You may need to modify the script to use a different I2C bus if your hardware differs from the default configuration

## Configuration

### Environment Variables

The following environment variables can be set to customize the stream:

| Variable          | Default      | Description                                        |
|-------------------|--------------|---------------------------------------------------|
| DISPLAY           | :0.0         | X11 display to capture                            |
| RESOLUTION        | 1920x1080    | Target resolution (auto-detects and adjusts)      |
| FRAMERATE         | 60           | Frames per second                                 |
| BITRATE           | 6M           | Video bitrate                                     |
| HTTP_PORT         | 8080         | HTTP server port                                  |
| AUDIO_ENABLED     | false        | Enable audio streaming                            |
| AUDIO_BITRATE     | 128          | Audio bitrate (kbps)                              |
| AUDIO_CODEC       | aac          | Audio codec (aac, mp3, pcm)                       |
| AUDIO_SAMPLE_RATE | 44100        | Sample rate for PCM audio                         |
| AUDIO_BIT_DEPTH   | 16           | Bit depth for PCM audio                           |

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
