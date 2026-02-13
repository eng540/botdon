import yt_dlp
import uuid
import os
import time
import random

# ================ الإعدادات ================
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

MAX_RETRIES = 3
RETRY_DELAY = 3

# قائمة User-Agents حقيقية للتغيير العشوائي
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_random_headers():
    """إنشاء هيدرات عشوائية تشبه المتصفح"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

def get_available_format(url):
    """محاولة الحصول على الصيغ المتوفرة أولاً"""
    try:
        ydl = yt_dlp.YoutubeDL({"quiet": True})
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        
        # البحث عن صيغة متوفرة مع فيديو وصوت
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                if f.get('filesize', 0) < 50 * 1024 * 1024:  # أقل من 50MB
                    return f['format_id']
        
        # إذا ما لقينا، خذ أول صيغة
        if formats:
            return formats[0]['format_id']
    except:
        pass
    return None

def download_video(url: str):
    """
    تحميل الفيديو مع حلول لمشكلة 403 والصيغ غير المتوفرة
    """
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # محاولة معرفة الصيغة المناسبة أولاً
    preferred_format = get_available_format(url)
    
    # قائمة الصيغ للمحاولة (مرتبة حسب الأفضلية)
    format_specs = [
        preferred_format if preferred_format else "best[ext=mp4]",  # الصيغة المناسبة
        "best[height<=720][ext=mp4]",  # 720p بصيغة MP4
        "best[height<=480][ext=mp4]",  # 480p بصيغة MP4
        "best",  # أي صيغة متوفرة
        "worst",  # أسوأ جودة كحل أخير
    ]
    
    for attempt in range(MAX_RETRIES):
        for format_spec in format_specs[:attempt+2]:  # جرب صيغ أكثر مع كل محاولة
            try:
                print(f"🔄 محاولة {attempt + 1}/{MAX_RETRIES} - الصيغة: {format_spec}")
                
                # إعدادات متغيرة حسب المحاولة
                ydl_opts = {
                    "outtmpl": filepath,
                    "format": format_spec,
                    "quiet": True,
                    "no_warnings": True,
                    
                    # إعدادات إعادة المحاولة
                    "retries": 10,
                    "fragment_retries": 10,
                    "socket_timeout": 30,
                    
                    # إعدادات التوافق
                    "noplaylist": True,
                    "geo_bypass": True,
                    "nocheckcertificate": True,
                    "ignoreerrors": True,
                    
                    # بصمة متصفح متغيرة (لمنع 403)
                    "http_headers": get_random_headers(),
                    
                    # تجاوز مشاكل الشبكة
                    "source_address": "0.0.0.0",
                    
                    # إعدادات إضافية
                    "extract_flat": False,
                    "force_generic_extractor": False,
                }
                
                # إضافة الكوكيز إذا وجدت
                if os.path.exists("cookies.txt"):
                    ydl_opts["cookiefile"] = "cookies.txt"
                
                # محاولة التحميل
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # التحقق من نجاح التحميل
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)
                    print(f"✅ تم التحميل بنجاح: {size_mb:.2f} MB")
                    return filepath
                
            except Exception as e:
                print(f"❌ فشل بالصيغة {format_spec}: {str(e)[:50]}...")
                
                # إذا كان خطأ 403، غير User-Agent
                if "403" in str(e):
                    print("⚠️ خطأ 403 - تغيير User-Agent...")
                    time.sleep(1)
                    continue
                    
                # إذا كان خطأ الصيغة غير متوفرة، جرب الصيغة التالية
                elif "format is not available" in str(e):
                    print("⚠️ الصيغة غير متوفرة - نجرب صيغة أخرى...")
                    continue
        
        # انتظار قبل المحاولة التالية
        if attempt < MAX_RETRIES - 1:
            wait_time = RETRY_DELAY * (attempt + 1)
            print(f"⏳ انتظار {wait_time} ثواني قبل المحاولة التالية...")
            time.sleep(wait_time)
    
    # فشلت كل المحاولات
    return None

def download_with_fallback(url: str):
    """
    دالة متقدمة مع خيارات احتياطية متعددة
    """
    # المحاولة الأولى: الإعدادات العادية
    result = download_video(url)
    if result:
        return result
    
    # المحاولة الثانية: استخدام yt-dlp مباشرة بدون إعدادات مخصصة
    print("🔄 محاولة بدون إعدادات مخصصة...")
    try:
        filename = f"{uuid.uuid4()}.mp4"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        os.system(f"yt-dlp -f best -o '{filepath}' '{url}'")
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return filepath
    except:
        pass
    
    # المحاولة الثالثة: استخدام yt-dlp مع أمر خارجي
    print("🔄 محاولة بأمر خارجي...")
    try:
        filename = f"{uuid.uuid4()}.mp4"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        cmd = f"yt-dlp --user-agent 'Mozilla/5.0' --format best --output '{filepath}' '{url}'"
        os.system(cmd)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return filepath
    except:
        pass
    
    return None

def cleanup_old_files(max_age_minutes: int = 30):
    """
    تنظيف الملفات القديمة (أسرع لمنع تراكم الملفات)
    """
    now = time.time()
    count = 0
    
    for filename in os.listdir(DOWNLOAD_DIR):
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getctime(filepath)
            if file_age > max_age_minutes * 60:
                try:
                    os.remove(filepath)
                    count += 1
                except:
                    pass
    
    if count > 0:
        print(f"🧹 تم حذف {count} ملف/ملفات قديمة")