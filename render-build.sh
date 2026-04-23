#!/usr/bin/env bash
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Create a directory for ffmpeg if it doesn't exist
mkdir -p ffmpeg

# Download and extract FFmpeg static binaries
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar xJ -C ffmpeg --strip-components 1

# Make sure the binary is executable
chmod +x ffmpeg/ffmpeg
