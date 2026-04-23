import os
import asyncio
import logging
import yt_dlp
import sys
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import subprocess
import shutil

def ensure_ffmpeg():
    """Checks for FFmpeg and installs it if missing (Only for Render Linux environment)"""
    ffmpeg_bin = os.path.join(os.getcwd(), "ffmpeg", "ffmpeg")
    
    if not os.path.exists(ffmpeg_bin):
        print("⚠️ FFmpeg not found! Starting emergency installation...", flush=True)
        try:
            # Create directory
            os.makedirs("ffmpeg", exist_ok=True)
            # Download and extract in one command
            cmd = (
                "curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | "
                "tar xJ -C ffmpeg --strip-components=1"
            )
            subprocess.run(cmd, shell=True, check=True)
            # Give execution permissions
            subprocess.run("chmod -R +x ffmpeg/", shell=True, check=True)
            print("✅ FFmpeg emergency installation successful!", flush=True)
        except Exception as e:
            print(f"❌ Emergency installation failed: {e}", flush=True)
    else:
        print(f"✅ FFmpeg is already present at: {ffmpeg_bin}", flush=True)

# --- LOGGING CONFIGURATION ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- WEB SERVER FOR UPTIME (KEEP ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "Universal Downloader Bot is Active!"

def run_flask():
    # Render dynamic port binding
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def start_keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- CONFIGURATION & PATHS ---
TOKEN = os.getenv("TOKEN")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg")
FFMPEG_PATH = os.path.join(FFMPEG_DIR, "ffmpeg")

# Dynamic PATH integration for Linux environments
if FFMPEG_DIR not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + FFMPEG_DIR

# --- CORE ENGINE: MEDIA DOWNLOADER ---
def download_media(url, mode, quality='720'):
    """Handles extraction and merging using yt-dlp and verified FFmpeg path."""
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    # Path Verification Log
    if not os.path.exists(FFMPEG_PATH):
        logger.error(f"FFmpeg binary not found at {FFMPEG_PATH}")
        raise FileNotFoundError("FFmpeg binary missing on server.")

    ydl_opts = {
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'ffmpeg_location': FFMPEG_PATH,
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    # YouTube engelini aşmak için alternatif istemci kullan:
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}}, 
    'prefer_ffmpeg': True,
}
    }

    if mode == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        res = quality if quality in ['480', '720', '1080'] else 'best'
        ydl_opts.update({
            'format': f'bestvideo[height<={res}]+bestaudio/best/best[height<={res}]',
            'merge_output_format': 'mp4',
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filename)
        
        # Extension handling after FFmpeg processing
        final_ext = ".mp3" if mode == 'audio' else ".mp4"
        return f"{base}{final_ext}"

# --- TELEGRAM BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "<b>Universal Media Downloader</b> 🚀\n\n"
        "Download videos/audio from 1000+ platforms.\n"
        "Simply send a link to start."
    )
    await update.message.reply_html(welcome_text)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return
    
    context.user_data['url'] = url
    keyboard = [
        [InlineKeyboardButton("🎬 Video", callback_data='v_menu')],
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data='a_dl')]
    ]
    await update.message.reply_text("Select conversion format:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('url')

    if query.data == 'v_menu':
        keyboard = [
            [InlineKeyboardButton("1080p", callback_data='v_1080'),
             InlineKeyboardButton("720p", callback_data='v_720')],
            [InlineKeyboardButton("480p", callback_data='v_480')]
        ]
        await query.edit_message_text("Select Video Quality:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    else:
        status_msg = await query.edit_message_text("⚡ Processing... Please wait.")
        try:
            mode = 'audio' if query.data == 'a_dl' else 'video'
            quality = query.data.split('_')[1] if mode == 'video' else None
            
            loop = asyncio.get_event_loop()
            file_path = await loop.run_in_executor(None, download_media, url, mode, quality)

            await query.message.reply_chat_action("upload_document")
            with open(file_path, 'rb') as f:
                await query.message.reply_document(document=f, caption="✅ Processed Successfully.")
            
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Download error: {e}")
            await query.message.reply_text(f"❌ Error: {str(e)[:100]}")

# --- APPLICATION ENTRY POINT ---
async def main():
    if not TOKEN:
        logger.error("No TOKEN environment variable found!")
        return

    start_keep_alive()
    
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    bot_app.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("Bot is starting...")
    await bot_app.initialize()
    await bot_app.updater.start_polling()
    await bot_app.start()
    
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot Stopped.")
