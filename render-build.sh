#!/usr/bin/env bash
set -e

# Install python dependencies
pip install -r requirements.txt

# Download and extract FFmpeg static binaries
mkdir -p ffmpeg
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar xJ -C ffmpeg --strip-components=1
