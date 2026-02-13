import yt_dlp
import uuid
import os
import time

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_video(url: str):
    filename = f"{uuid.uuid4()}.mp4"
    output = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        "outtmpl": output,
        "format": "best",
        "noplaylist": True,
        "quiet": True,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 60,
        "nocheckcertificate": True,
        "ignoreerrors": True,

        # بصمة متصفح حقيقي لمنع 403
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9",
        },

        # تجنب مشاكل IPv6 في السحابة
        "source_address": "0.0.0.0",
    }

    for attempt in range(3):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if os.path.exists(output):
                return output

        except Exception:
            time.sleep(5)

    return None