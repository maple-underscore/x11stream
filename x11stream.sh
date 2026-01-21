#!/bin/bash
#
# x11stream.sh - Stream X11 display via HTTP using ffmpeg
#
# This script captures the X11 display and makes it available via HTTP
# Access the stream at: http://{ip}:8080/stream
#
# Run with --interactive or -i for interactive mode
# Run without arguments for non-interactive mode using environment variables
#

set -e

# ============================================
# Audio Presets with Bandwidth Estimates
# ============================================
# MP3/AAC Bitrate Options:
#   64 kbps  - Low quality voice (~8 KB/s)
#   128 kbps - Standard quality (~16 KB/s)
#   192 kbps - Good quality (~24 KB/s)
#   256 kbps - High quality (~32 KB/s)
#   320 kbps - Maximum MP3 quality (~40 KB/s)
#
# PCM/Lossless Options (sample rate @ bit depth):
#   16-bit @ 44.1 kHz - CD quality (~172 KB/s stereo)
#   16-bit @ 48 kHz   - DVD quality (~188 KB/s stereo)
#   16-bit @ 96 kHz   - Hi-Res (~375 KB/s stereo)
#   16-bit @ 192 kHz  - Ultra Hi-Res (~750 KB/s stereo)
#   24-bit @ 44.1 kHz - Studio quality (~258 KB/s stereo)
#   24-bit @ 48 kHz   - Professional (~281 KB/s stereo)
#   24-bit @ 96 kHz   - Hi-Res Studio (~563 KB/s stereo)
#   24-bit @ 192 kHz  - Ultra Hi-Res Studio (~1125 KB/s stereo)
# ============================================

# Default configuration
DISPLAY_NUM="${DISPLAY:-:0.0}"
TARGET_RESOLUTION="${RESOLUTION:-1920x1080}"
FRAMERATE="${FRAMERATE:-60}"
VIDEO_BITRATE="${BITRATE:-6M}"
HTTP_PORT="${HTTP_PORT:-8080}"
AUDIO_ENABLED="${AUDIO_ENABLED:-false}"
AUDIO_BITRATE="${AUDIO_BITRATE:-128}"
AUDIO_SAMPLE_RATE="${AUDIO_SAMPLE_RATE:-44100}"
AUDIO_BIT_DEPTH="${AUDIO_BIT_DEPTH:-16}"
AUDIO_CODEC="${AUDIO_CODEC:-aac}"
AUDIO_SOURCE="${AUDIO_SOURCE:-default}"
INTERACTIVE_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interactive)
            INTERACTIVE_MODE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -i, --interactive    Run in interactive mode"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Environment variables (non-interactive mode):"
            echo "  DISPLAY          X11 display (default: :0.0)"
            echo "  RESOLUTION       Target video resolution (default: 1920x1080)"
            echo "                   Auto-detects display resolution and scales down if needed"
            echo "  FRAMERATE        Frames per second (default: 60)"
            echo "  BITRATE          Video bitrate (default: 6M)"
            echo "  HTTP_PORT        HTTP server port (default: 8080)"
            echo "  AUDIO_ENABLED    Enable audio (default: false)"
            echo "  AUDIO_BITRATE    Audio bitrate in kbps (default: 128)"
            echo "  AUDIO_CODEC      Audio codec: aac, mp3, pcm (default: aac)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Detect the machine's IP address
# Uses 'ip route get 1' to determine the primary interface IP via the default route
get_ip() {
    ip route get 1 2>/dev/null | awk '{print $7; exit}' || hostname -I | awk '{print $1}'
}

IP_ADDRESS=$(get_ip)

# Validate IP address
if [ -z "$IP_ADDRESS" ]; then
    echo "Error: Unable to determine IP address for this host." >&2
    echo "Please ensure that 'ip route' or 'hostname -I' is available, or set IP_ADDRESS manually." >&2
    exit 1
fi

# Detect display resolution using xdpyinfo
# Returns resolution in WIDTHxHEIGHT format (e.g., 1920x1080)
get_display_resolution() {
    local display="$1"
    local resolution
    resolution=$(xdpyinfo -display "$display" 2>/dev/null | grep 'dimensions:' | awk '{print $2}' | head -1)
    # Validate that the resolution matches WIDTHxHEIGHT format
    if [[ "$resolution" =~ ^[0-9]+x[0-9]+$ ]]; then
        echo "$resolution"
    else
        echo ""
    fi
}

# Parse resolution string into width and height
# Usage: parse_resolution "1920x1080" -> prints "1920 1080"
# Returns empty string if format is invalid
parse_resolution() {
    local res="$1"
    if [[ "$res" =~ ^([0-9]+)x([0-9]+)$ ]]; then
        echo "${BASH_REMATCH[1]} ${BASH_REMATCH[2]}"
    else
        echo ""
    fi
}

# Compare resolutions and determine output resolution and scaling needs
# Returns: CAPTURE_RESOLUTION (what to capture) and SCALE_FILTER (ffmpeg filter if needed)
determine_resolution() {
    local detected_res="$1"
    local target_res="$2"
    
    if [ -z "$detected_res" ]; then
        echo "Warning: Could not detect display resolution, using target resolution: $target_res" >&2
        CAPTURE_RESOLUTION="$target_res"
        SCALE_FILTER=""
        OUTPUT_RESOLUTION="$target_res"
        return
    fi
    
    # Parse detected resolution
    local detected_parsed target_parsed
    detected_parsed=$(parse_resolution "$detected_res")
    target_parsed=$(parse_resolution "$target_res")
    
    # Validate parsed resolutions
    if [ -z "$detected_parsed" ] || [ -z "$target_parsed" ]; then
        echo "Warning: Invalid resolution format, using target resolution: $target_res" >&2
        CAPTURE_RESOLUTION="$target_res"
        SCALE_FILTER=""
        OUTPUT_RESOLUTION="$target_res"
        return
    fi
    
    read -r detected_width detected_height <<< "$detected_parsed"
    read -r target_width target_height <<< "$target_parsed"
    
    # Calculate pixel counts for comparison
    local detected_pixels=$((detected_width * detected_height))
    local target_pixels=$((target_width * target_height))
    
    if [ "$detected_pixels" -gt "$target_pixels" ]; then
        # Detected resolution is higher than target - capture full and scale down
        CAPTURE_RESOLUTION="$detected_res"
        SCALE_FILTER="-vf scale=${target_width}:${target_height}"
        OUTPUT_RESOLUTION="$target_res"
        echo "Detected resolution ($detected_res) is higher than target ($target_res), will scale down" >&2
    else
        # Detected resolution is lower or equal - use detected resolution
        CAPTURE_RESOLUTION="$detected_res"
        SCALE_FILTER=""
        OUTPUT_RESOLUTION="$detected_res"
        if [ "$detected_pixels" -lt "$target_pixels" ]; then
            echo "Detected resolution ($detected_res) is lower than target ($target_res), using native resolution" >&2
        fi
    fi
}


# Calculate bandwidth estimate
calculate_bandwidth() {
    local video_bps audio_bps total_kbps
    
    # Parse video bitrate (e.g., "6M" -> 6000 kbps)
    case "$VIDEO_BITRATE" in
        *M) video_bps=$((${VIDEO_BITRATE%M} * 1000)) ;;
        *k) video_bps=${VIDEO_BITRATE%k} ;;
        *)  video_bps=$VIDEO_BITRATE ;;  # Assume kbps if no suffix
    esac
    
    # Calculate audio bandwidth in kbps
    if [ "$AUDIO_ENABLED" = "true" ]; then
        if [ "$AUDIO_CODEC" = "pcm" ]; then
            # PCM: sample_rate * bit_depth * channels / 1000 = kbps
            audio_bps=$((AUDIO_SAMPLE_RATE * AUDIO_BIT_DEPTH * 2 / 1000))
        else
            audio_bps=$AUDIO_BITRATE
        fi
    else
        audio_bps=0
    fi
    
    total_kbps=$((video_bps + audio_bps))
    echo "$total_kbps kbps (~$((total_kbps / 8)) KB/s)"
}

# Show audio presets menu
show_audio_presets() {
    echo ""
    echo "Audio Quality Presets:"
    echo "============================================"
    echo "Lossy Compression (AAC/MP3):"
    echo "  1)  64 kbps  - Voice/Low quality     (~8 KB/s)"
    echo "  2) 128 kbps  - Standard quality      (~16 KB/s)"
    echo "  3) 192 kbps  - Good quality          (~24 KB/s)"
    echo "  4) 256 kbps  - High quality          (~32 KB/s)"
    echo "  5) 320 kbps  - Maximum quality       (~40 KB/s)"
    echo ""
    echo "Lossless PCM (16-bit):"
    echo "  6) 16-bit @ 44.1 kHz - CD quality    (~172 KB/s)"
    echo "  7) 16-bit @ 48 kHz   - DVD quality   (~188 KB/s)"
    echo "  8) 16-bit @ 96 kHz   - Hi-Res        (~375 KB/s)"
    echo "  9) 16-bit @ 192 kHz  - Ultra Hi-Res  (~750 KB/s)"
    echo ""
    echo "Lossless PCM (24-bit):"
    echo " 10) 24-bit @ 44.1 kHz - Studio        (~258 KB/s)"
    echo " 11) 24-bit @ 48 kHz   - Professional  (~281 KB/s)"
    echo " 12) 24-bit @ 96 kHz   - Hi-Res Studio (~563 KB/s)"
    echo " 13) 24-bit @ 192 kHz  - Ultra Hi-Res  (~1125 KB/s)"
    echo "============================================"
}

# Apply audio preset
apply_audio_preset() {
    case $1 in
        1)  AUDIO_CODEC="aac"; AUDIO_BITRATE=64 ;;
        2)  AUDIO_CODEC="aac"; AUDIO_BITRATE=128 ;;
        3)  AUDIO_CODEC="aac"; AUDIO_BITRATE=192 ;;
        4)  AUDIO_CODEC="aac"; AUDIO_BITRATE=256 ;;
        5)  AUDIO_CODEC="aac"; AUDIO_BITRATE=320 ;;
        6)  AUDIO_CODEC="pcm"; AUDIO_BIT_DEPTH=16; AUDIO_SAMPLE_RATE=44100 ;;
        7)  AUDIO_CODEC="pcm"; AUDIO_BIT_DEPTH=16; AUDIO_SAMPLE_RATE=48000 ;;
        8)  AUDIO_CODEC="pcm"; AUDIO_BIT_DEPTH=16; AUDIO_SAMPLE_RATE=96000 ;;
        9)  AUDIO_CODEC="pcm"; AUDIO_BIT_DEPTH=16; AUDIO_SAMPLE_RATE=192000 ;;
        10) AUDIO_CODEC="pcm"; AUDIO_BIT_DEPTH=24; AUDIO_SAMPLE_RATE=44100 ;;
        11) AUDIO_CODEC="pcm"; AUDIO_BIT_DEPTH=24; AUDIO_SAMPLE_RATE=48000 ;;
        12) AUDIO_CODEC="pcm"; AUDIO_BIT_DEPTH=24; AUDIO_SAMPLE_RATE=96000 ;;
        13) AUDIO_CODEC="pcm"; AUDIO_BIT_DEPTH=24; AUDIO_SAMPLE_RATE=192000 ;;
        *)  echo "Invalid selection, using default (128 kbps AAC)"; AUDIO_CODEC="aac"; AUDIO_BITRATE=128 ;;
    esac
}

# Interactive configuration
interactive_setup() {
    echo "============================================"
    echo "X11 Stream Server - Interactive Setup"
    echo "============================================"
    echo ""
    
    # Display selection
    echo "Current X11 display: $DISPLAY_NUM"
    read -p "Enter display (press Enter for default): " input
    [ -n "$input" ] && DISPLAY_NUM="$input"
    
    # Resolution selection
    echo ""
    echo "Target Resolution Options (auto-detection will adjust if display is smaller):"
    echo "  1) 1920x1080 (Full HD)"
    echo "  2) 2560x1440 (2K/QHD)"
    echo "  3) 3840x2160 (4K/UHD)"
    echo "  4) 1280x720 (HD)"
    echo "  5) 1366x768 (HD+)"
    echo "  6) Custom"
    read -p "Select resolution [1-6] (default: 1): " res_choice
    case $res_choice in
        2) TARGET_RESOLUTION="2560x1440" ;;
        3) TARGET_RESOLUTION="3840x2160" ;;
        4) TARGET_RESOLUTION="1280x720" ;;
        5) TARGET_RESOLUTION="1366x768" ;;
        6) read -p "Enter custom resolution (e.g., 1920x1080): " TARGET_RESOLUTION ;;
        *) TARGET_RESOLUTION="1920x1080" ;;
    esac
    
    # Framerate selection
    echo ""
    echo "Framerate Options:"
    echo "  1) 24 fps (Film)"
    echo "  2) 30 fps (Standard)"
    echo "  3) 60 fps (Smooth)"
    echo "  4) 120 fps (High refresh)"
    echo "  5) 144 fps (Gaming)"
    echo "  6) Custom"
    read -p "Select framerate [1-6] (default: 3): " fps_choice
    case $fps_choice in
        1) FRAMERATE=24 ;;
        2) FRAMERATE=30 ;;
        4) FRAMERATE=120 ;;
        5) FRAMERATE=144 ;;
        6) read -p "Enter custom framerate: " FRAMERATE ;;
        *) FRAMERATE=60 ;;
    esac
    
    # Video quality/bitrate selection
    echo ""
    echo "Video Quality Options:"
    echo "  1) 2M  - Low bandwidth    (~250 KB/s)"
    echo "  2) 4M  - Medium quality   (~500 KB/s)"
    echo "  3) 6M  - Good quality     (~750 KB/s)"
    echo "  4) 10M - High quality     (~1.25 MB/s)"
    echo "  5) 15M - Very high        (~1.9 MB/s)"
    echo "  6) 20M - Excellent        (~2.5 MB/s)"
    echo "  7) Custom"
    read -p "Select video quality [1-7] (default: 3): " quality_choice
    case $quality_choice in
        1) VIDEO_BITRATE="2M" ;;
        2) VIDEO_BITRATE="4M" ;;
        4) VIDEO_BITRATE="10M" ;;
        5) VIDEO_BITRATE="15M" ;;
        6) VIDEO_BITRATE="20M" ;;
        7) read -p "Enter custom bitrate (e.g., 6M or 6000k): " VIDEO_BITRATE ;;
        *) VIDEO_BITRATE="6M" ;;
    esac
    
    # Audio configuration
    echo ""
    read -p "Enable audio streaming? [y/N]: " audio_choice
    if [[ "$audio_choice" =~ ^[Yy]$ ]]; then
        AUDIO_ENABLED="true"
        
        show_audio_presets
        read -p "Select audio preset [1-13] (default: 2): " audio_preset
        [ -z "$audio_preset" ] && audio_preset=2
        apply_audio_preset "$audio_preset"
        
        # Audio source
        echo ""
        echo "Audio Source:"
        echo "  1) PulseAudio default"
        echo "  2) ALSA default"
        echo "  3) Custom"
        read -p "Select audio source [1-3] (default: 1): " source_choice
        case $source_choice in
            2) AUDIO_SOURCE="hw:0" ;;
            3) read -p "Enter audio source: " AUDIO_SOURCE ;;
            *) AUDIO_SOURCE="default" ;;
        esac
    else
        AUDIO_ENABLED="false"
    fi
    
    # HTTP Port
    echo ""
    read -p "HTTP port (default: 8080): " port_input
    [ -n "$port_input" ] && HTTP_PORT="$port_input"
    
    echo ""
    echo "============================================"
    echo "Configuration Summary"
    echo "============================================"
}

# Run interactive setup if requested
if [ "$INTERACTIVE_MODE" = "true" ]; then
    interactive_setup
fi

# Build audio arguments
build_audio_args() {
    if [ "$AUDIO_ENABLED" = "true" ]; then
        local audio_input audio_codec_args
        
        # Input source
        if [ "$AUDIO_SOURCE" = "default" ]; then
            audio_input="-f pulse -i default"
        else
            audio_input="-f alsa -i $AUDIO_SOURCE"
        fi
        
        # Codec settings
        if [ "$AUDIO_CODEC" = "pcm" ]; then
            local fmt
            if [ "$AUDIO_BIT_DEPTH" = "24" ]; then
                fmt="s24le"
            else
                fmt="s16le"
            fi
            audio_codec_args="-c:a pcm_${fmt} -ar $AUDIO_SAMPLE_RATE"
        else
            audio_codec_args="-c:a $AUDIO_CODEC -b:a ${AUDIO_BITRATE}k"
        fi
        
        echo "$audio_input $audio_codec_args"
    fi
}

# Detect display resolution and determine capture/output settings
DETECTED_RESOLUTION=$(get_display_resolution "$DISPLAY_NUM")
determine_resolution "$DETECTED_RESOLUTION" "$TARGET_RESOLUTION"

# Display configuration
echo "Display:     $DISPLAY_NUM"
if [ -n "$DETECTED_RESOLUTION" ]; then
    echo "Detected:    $DETECTED_RESOLUTION"
fi
echo "Target:      $TARGET_RESOLUTION"
if [ -n "$SCALE_FILTER" ]; then
    echo "Output:      $OUTPUT_RESOLUTION (scaled down)"
else
    echo "Output:      $OUTPUT_RESOLUTION"
fi
echo "Framerate:   $FRAMERATE fps"
echo "Video:       $VIDEO_BITRATE"
if [ "$AUDIO_ENABLED" = "true" ]; then
    if [ "$AUDIO_CODEC" = "pcm" ]; then
        echo "Audio:       PCM ${AUDIO_BIT_DEPTH}-bit @ ${AUDIO_SAMPLE_RATE} Hz"
    else
        audio_codec_upper=$(echo "$AUDIO_CODEC" | tr '[:lower:]' '[:upper:]')
        echo "Audio:       ${audio_codec_upper} @ ${AUDIO_BITRATE} kbps"
    fi
else
    echo "Audio:       Disabled"
fi
echo "HTTP Port:   $HTTP_PORT"
echo ""
echo "Estimated bandwidth: $(calculate_bandwidth)"
echo ""
echo "Access your stream at:"
echo "  http://${IP_ADDRESS}:${HTTP_PORT}/stream"
echo "  http://localhost:${HTTP_PORT}/stream"
echo "============================================"

# Build and execute ffmpeg command
AUDIO_ARGS=$(build_audio_args)

# Build scale filter argument if scaling is needed
if [ -n "$SCALE_FILTER" ]; then
    VIDEO_FILTER_ARGS="$SCALE_FILTER"
else
    VIDEO_FILTER_ARGS=""
fi

# Run ffmpeg with x11grab and output to HTTP via mpegts
# The -listen 1 flag makes ffmpeg act as an HTTP server
# Low-latency settings:
#   -probesize 32768: Minimal probe size (32KB) for faster stream start
#   -analyzeduration 0: Skip analysis delay for immediate processing
if [ "$AUDIO_ENABLED" = "true" ]; then
    exec ffmpeg -fflags nobuffer -flags low_delay -probesize 32768 -analyzeduration 0 \
        -f x11grab -video_size "$CAPTURE_RESOLUTION" -framerate "$FRAMERATE" -i "$DISPLAY_NUM" \
        $AUDIO_ARGS \
        ${VIDEO_FILTER_ARGS:+$VIDEO_FILTER_ARGS} \
        -c:v libx264 -preset ultrafast -tune zerolatency \
        -x264-params "bframes=0:rc-lookahead=0:sync-lookahead=0:sliced-threads=1" \
        -g 15 -keyint_min 15 -sc_threshold 0 \
        -b:v "$VIDEO_BITRATE" -maxrate "$VIDEO_BITRATE" -bufsize 256k \
        -pix_fmt yuv420p \
        -f mpegts \
        -listen 1 "http://0.0.0.0:${HTTP_PORT}/stream"
else
    exec ffmpeg -fflags nobuffer -flags low_delay -probesize 32768 -analyzeduration 0 \
        -f x11grab -video_size "$CAPTURE_RESOLUTION" -framerate "$FRAMERATE" -i "$DISPLAY_NUM" \
        ${VIDEO_FILTER_ARGS:+$VIDEO_FILTER_ARGS} \
        -c:v libx264 -preset ultrafast -tune zerolatency \
        -x264-params "bframes=0:rc-lookahead=0:sync-lookahead=0:sliced-threads=1" \
        -g "$(((FRAMERATE/10)>0?(FRAMERATE/10):1))" -keyint_min 15 -sc_threshold 0 \
        -b:v "$VIDEO_BITRATE" -maxrate "$VIDEO_BITRATE" -bufsize 256k \
        -pix_fmt yuv420p \
        -f mpegts \
        -listen 1 "http://0.0.0.0:${HTTP_PORT}/stream"
fi
