#!/bin/bash
#
# x11stream-wrapper.sh - Wrapper script for x11stream with auto-restart
#
# This script runs x11stream and automatically restarts it if it crashes
# Designed to be used with systemd service
#

set -e

SCRIPT_DIR="/usr/local/bin"
RESTART_DELAY="${RESTART_DELAY:-5}"
MAX_RESTARTS="${MAX_RESTARTS:-0}"  # 0 = unlimited
restart_count=0

echo "Starting x11stream with auto-restart capability"
echo "Restart delay: ${RESTART_DELAY}s"
if [ "$MAX_RESTARTS" -eq 0 ]; then
    echo "Max restarts: unlimited"
else
    echo "Max restarts: $MAX_RESTARTS"
fi

while true; do
    echo "=========================================="
    echo "Starting x11stream (attempt $((restart_count + 1)))"
    echo "$(date)"
    echo "=========================================="
    
    # Run x11stream.sh and capture exit code
    set +e
    "$SCRIPT_DIR/x11stream.sh"
    exit_code=$?
    set -e
    
    echo "=========================================="
    echo "x11stream exited with code: $exit_code"
    echo "$(date)"
    echo "=========================================="
    
    # Increment restart counter
    restart_count=$((restart_count + 1))
    
    # Check if max restarts reached
    if [ "$MAX_RESTARTS" -ne 0 ] && [ "$restart_count" -ge "$MAX_RESTARTS" ]; then
        echo "Max restart attempts reached ($MAX_RESTARTS), exiting"
        exit $exit_code
    fi
    
    # Exit on clean shutdown (exit code 0)
    if [ $exit_code -eq 0 ]; then
        echo "Clean exit detected, not restarting"
        exit 0
    fi
    
    echo "Restarting in ${RESTART_DELAY} seconds..."
    sleep "$RESTART_DELAY"
done
