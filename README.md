# x11stream

Shell script on Ubuntu to auto-stream X11 display on boot using x11grab and ffmpeg.

## Features

- Captures X11 display using ffmpeg with low-latency settings
- Hosts an HTTP server for direct browser/VLC access
- Auto-starts on boot via systemd service
- Configurable resolution, framerate, and bitrate

## Requirements

- Ubuntu (or other Linux with X11)
- ffmpeg with x11grab support
- systemd (for auto-start on boot)

Install ffmpeg:
```bash
sudo apt update
sudo apt install ffmpeg
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

### Manual Start
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

The following environment variables can be set to customize the stream:

| Variable    | Default      | Description                    |
|-------------|--------------|--------------------------------|
| DISPLAY     | :0.0         | X11 display to capture         |
| RESOLUTION  | 1920x1080    | Capture resolution             |
| FRAMERATE   | 30           | Frames per second              |
| BITRATE     | 6M           | Video bitrate                  |
| HTTP_PORT   | 8080         | HTTP server port               |

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

## License

MIT License
