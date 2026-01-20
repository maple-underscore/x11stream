# x11stream

Shell script on Ubuntu to auto-stream X11 display on boot using x11grab and ffmpeg.

## Features

- Captures X11 display using ffmpeg with low-latency settings
- Hosts an HTTP server for direct browser/VLC access
- Auto-starts on boot via systemd service
- **Interactive mode** for easy configuration
- **Audio streaming support** with multiple quality presets
- Configurable resolution, framerate, bitrate, and audio settings
- Bandwidth estimation for all configurations

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

Configure ffmpeg to use x11grab and libx264:
```bash
sudo ./configure --enable-x11grab --enable-libx264
```

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

## Configuration

### Environment Variables

The following environment variables can be set to customize the stream:

| Variable          | Default      | Description                    |
|-------------------|--------------|--------------------------------|
| DISPLAY           | :0.0         | X11 display to capture         |
| RESOLUTION        | 1920x1080    | Capture resolution             |
| FRAMERATE         | 60           | Frames per second              |
| BITRATE           | 6M           | Video bitrate                  |
| HTTP_PORT         | 8080         | HTTP server port               |
| AUDIO_ENABLED     | false        | Enable audio streaming         |
| AUDIO_BITRATE     | 128          | Audio bitrate (kbps)           |
| AUDIO_CODEC       | aac          | Audio codec (aac, mp3, pcm)    |
| AUDIO_SAMPLE_RATE | 44100        | Sample rate for PCM audio      |
| AUDIO_BIT_DEPTH   | 16           | Bit depth for PCM audio        |

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
Ensure X11 is running and the `DISPLAY` variable is set correctly. On systems with multiple displays, try `:1.0` or `:0.1`.

### "Permission denied" error
The user running the script needs access to the X11 display. Run with appropriate permissions or add the user to the video group.

### Stream not accessible
- Check if ffmpeg is running: `ps aux | grep ffmpeg`
- Ensure the port is not blocked by firewall: `sudo ufw allow 8080/tcp`
- Verify the IP address and port in the startup output

### Audio not working
- Ensure PulseAudio or ALSA is running
- Check audio source: `pactl list short sources` (PulseAudio)
- Try different audio source in interactive mode

## License

MIT License
