#!/usr/bin/env bash
set -e

pip install -r requirements.txt

# Eski dosyaları temizle ve sıfırdan kur
rm -rf ffmpeg
mkdir -p ffmpeg

# FFmpeg indir
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o ffmpeg.tar.xz

# Dosyayı aç ve klasöre yerleştir
tar xf ffmpeg.tar.xz -C ffmpeg --strip-components=1

# Gereksiz paketi sil
rm ffmpeg.tar.xz

# Çalıştırma izni ver
chmod +x ffmpeg/ffmpeg ffmpeg/ffprobe
