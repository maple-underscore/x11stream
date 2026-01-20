#!/bin/bash
#
# x11stream.sh - Stream X11 display via HTTP using ffmpeg
#
# This script captures the X11 display and makes it available via HTTP
# Access the stream at: http://{ip}:8080/stream
#

set -e

# Configuration
DISPLAY_NUM="${DISPLAY:-:0.0}"
RESOLUTION="${RESOLUTION:-1920x1080}"
FRAMERATE="${FRAMERATE:-60}"
BITRATE="${BITRATE:-6M}"
HTTP_PORT="${HTTP_PORT:-8080}"

# Detect the machine's IP address
# Uses 'ip route get 1' to find the default route interface IP (1 is a dummy destination IP)
get_ip() {
    ip route get 1 2>/dev/null | awk '{print $7; exit}' || hostname -I | awk '{print $1}'
}

IP_ADDRESS=$(get_ip)

echo "============================================"
echo "X11 Stream Server"
echo "============================================"
echo "Display:     $DISPLAY_NUM"
echo "Resolution:  $RESOLUTION"
echo "Framerate:   $FRAMERATE fps"
echo "Bitrate:     $BITRATE"
echo "HTTP Port:   $HTTP_PORT"
echo ""
echo "Access your stream at:"
echo "  http://${IP_ADDRESS}:${HTTP_PORT}/stream"
echo "  http://localhost:${HTTP_PORT}/stream"
echo "============================================"

# Run ffmpeg with x11grab and output to HTTP via mpegts
# The -listen 1 flag makes ffmpeg act as an HTTP server
# Low-latency settings:
#   -probesize 32: Minimal probe size (bytes) for faster stream start
#   -analyzeduration 0: Skip analysis delay for immediate processing
exec ffmpeg -fflags nobuffer -flags low_delay -probesize 32 -analyzeduration 0 \
    -f x11grab -video_size "$RESOLUTION" -framerate "$FRAMERATE" -i "$DISPLAY_NUM" \
    -c:v libx264 -preset ultrafast -tune zerolatency \
    -x264-params "bframes=0:rc-lookahead=0:sync-lookahead=0:sliced-threads=1" \
    -g 15 -keyint_min 15 -sc_threshold 0 \
    -b:v "$BITRATE" -maxrate "$BITRATE" -bufsize 256k \
    -pix_fmt yuv420p \
    -f mpegts \
    -listen 1 "http://0.0.0.0:${HTTP_PORT}/stream"
