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
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,

        # استقرار التحميل
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,

        # تجاوز قيود بعض المواقع
        "noplaylist": True,
        "geo_bypass": True,
        "nocheckcertificate": True,

        # دعم Facebook وInstagram الخاص
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,

        # تحسين التوافق مع Railway
        "concurrent_fragment_downloads": 3,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(filepath):
            raise Exception("Download failed")

        return filepath

    except Exception as e:
        raise Exception(f"DOWNLOAD_ERROR: {str(e)}")