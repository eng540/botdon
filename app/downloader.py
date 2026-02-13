import yt_dlp
import uuid
import os
import time

# ================ الإعدادات ================
DOWNLOAD_DIR = "/tmp/downloads"  # مسار مؤقت (من الأولى) مع اسم أوضح
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

MAX_RETRIES = 3
RETRY_DELAY = 5

def download_video(url: str):
    """
    تحميل الفيديو بأفضل جودة مع إعادة محاولة ذكية
    """
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # إعدادات متقدمة (دمج مميزات النسختين)
    ydl_opts = {
        # إعدادات المخرجات (من الأولى)
        "outtmpl": filepath,
        "format": "bestvideo+bestaudio/best",  # أفضل جودة من الأولى
        "merge_output_format": "mp4",
        
        # إعدادات الهدوء (من الأولى)
        "quiet": True,
        "no_warnings": True,
        
        # إعدادات إعادة المحاولة (من الثانية - أرقام أعلى)
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 60,  # مهلة أطول من الثانية
        
        # إعدادات التوافق (من الأولى + الثانية)
        "noplaylist": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,  # من الثانية
        "source_address": "0.0.0.0",  # من الثانية
        
        # بصمة متصفح حقيقي (من الثانية)
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-us,en;q=0.5",
            "Sec-Fetch-Mode": "navigate",
        },
        
        # تحسين الأداء (من الأولى)
        "concurrent_fragment_downloads": 3,
        
        # الكوكيز (من الأولى)
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
    }
    
    # حلقة إعادة المحاولة (من الثانية)
    for attempt in range(MAX_RETRIES):
        try:
            print(f"🔄 محاولة {attempt + 1}/{MAX_RETRIES}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # محاولة استخراج المعلومات أولاً (تحسين)
                try:
                    info = ydl.extract_info(url, download=False)
                    if info and info.get('filesize', 0) > 500 * 1024 * 1024:  # أكبر من 500MB
                        print("⚠️ الفيديو كبير جداً، قد يفشل الرفع")
                except:
                    pass
                
                # التحميل الفعلي
                ydl.download([url])
            
            # التحقق من وجود الملف
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                file_size = os.path.getsize(filepath) / (1024 * 1024)
                print(f"✅ تم التحميل بنجاح: {file_size:.2f} MB")
                return filepath
            else:
                raise Exception("الملف فارغ أو غير موجود")
                
        except Exception as e:
            print(f"❌ خطأ في المحاولة {attempt + 1}: {e}")
            
            # محاولة أخيرة بصيغة مبسطة (مثل الثانية)
            if attempt == MAX_RETRIES - 2:
                print("🔄 محاولة بصيغة مبسطة...")
                ydl_opts["format"] = "best"
            
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    return None  # فشل كل المحاولات

def cleanup_old_files(max_age_hours: int = 24):
    """
    تنظيف الملفات القديمة تلقائياً
    """
    now = time.time()
    for filename in os.listdir(DOWNLOAD_DIR):
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getctime(filepath)
            if file_age > max_age_hours * 3600:
                try:
                    os.remove(filepath)
                    print(f"🧹 تم حذف ملف قديم: {filename}")
                except:
                    pass