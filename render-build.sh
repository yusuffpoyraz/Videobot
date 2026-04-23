#!/usr/bin/env bash
# Exit on error
set -e

# Install python dependencies
pip install -r requirements.txt

# Clean up any existing ffmpeg folder
rm -rf ffmpeg
mkdir -p ffmpeg

# Download static FFmpeg binaries
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o ffmpeg.tar.xz

# Extract and strip components to get binaries directly in /ffmpeg
tar xf ffmpeg.tar.xz -C ffmpeg --strip-components=1

# Cleanup
rm ffmpeg.tar.xz

# Grant execution permissions
chmod -R +x ffmpeg/
