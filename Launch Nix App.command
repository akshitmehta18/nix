#!/bin/bash
# Nix Web App & Live Support Launcher for macOS
# Created by Akshit Mehta & Nikhil Saini

echo "=========================================================="
echo "  🚀 Starting Nix Modern AI Assistant & Live Support Hub..."
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if command -v nix &> /dev/null; then
    nix app
else
    python3 "$SCRIPT_DIR/main.py" app
fi
