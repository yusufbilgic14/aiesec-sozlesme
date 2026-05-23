#!/bin/bash
# Install Microsoft TrueType Core Fonts on Linux (Debian/Ubuntu)
# Streamlit Cloud runs Ubuntu - this script runs before the app starts

if [ -f /usr/share/fonts/truetype/msttcorefonts/times.ttf ]; then
    echo "Fonts already installed."
    exit 0
fi

echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections 2>/dev/null || true
apt-get update -qq && apt-get install -y -qq ttf-mscorefonts-installer 2>/dev/null || true
fc-cache -f 2>/dev/null || true
echo "Font installation attempt complete."