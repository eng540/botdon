import yt_dlp
import os
import uuid

DOWNLOAD_DIR = "/tmp/videos"

def download_video(url: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        "outtmpl": filepath,
        "format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "socket_timeout": 20,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return filepath
