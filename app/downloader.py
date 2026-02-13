import yt_dlp
import uuid
import os
import time
import random

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

MAX_RETRIES = 3
RETRY_DELAY = 3

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
    }

def download_video(url: str):
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    formats = [
        "best[ext=mp4]",
        "best[height<=720][ext=mp4]",
        "best",
        "worst"
    ]

    for attempt in range(MAX_RETRIES):
        for fmt in formats:
            try:
                ydl_opts = {
                    "outtmpl": filepath,
                    "format": fmt,
                    "quiet": True,
                    "noplaylist": True,
                    "retries": 10,
                    "fragment_retries": 10,
                    "socket_timeout": 30,
                    "ignoreerrors": True,
                    "nocheckcertificate": True,
                    "geo_bypass": True,
                    "http_headers": get_headers(),
                    "source_address": "0.0.0.0",
                }

                if os.path.exists("cookies.txt"):
                    ydl_opts["cookiefile"] = "cookies.txt"

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    return filepath

            except Exception:
                continue

        time.sleep(RETRY_DELAY)

    return None

def cleanup_old_files(max_age_minutes=30):
    now = time.time()
    for f in os.listdir(DOWNLOAD_DIR):
        path = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(path):
            if now - os.path.getctime(path) > max_age_minutes * 60:
                try:
                    os.remove(path)
                except:
                    pass