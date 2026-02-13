import os
import asyncio
import time
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InputFile
from aiogram.exceptions import TelegramBadRequest
from downloader import download_video

# ================ الإعدادات ================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

RATE_LIMIT_SECONDS = 10  # مدة الانتظار بين الطلبات
MAX_RETRY_ATTEMPTS = 3    # عدد محاولات إعادة التحميل
RETRY_DELAY = 5           # التأخير بين المحاولات (ثواني)

# ================ تهيئة البوت ================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# تخزين آخر طلب لكل مستخدم
user_last_request = {}

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================ الدوال المساعدة ================
def is_supported_url(text: str) -> bool:
    """
    التحقق إذا كان الرابط من منصة مدعومة
    """
    if not text:
        return False
    
    domains = [
        "instagram.com",
        "tiktok.com",
        "facebook.com",
        "fb.com",
        "youtube.com",
        "youtu.be",
        "twitter.com",
        "x.com",
        "snapchat.com",
        "pinterest.com"
    ]
    return any(domain in text for domain in domains)

def get_platform_name(url: str) -> str:
    """
    تحديد اسم المنصة من الرابط
    """
    platforms = {
        "instagram": "انستغرام",
        "tiktok": "تيك توك",
        "facebook": "فيسبوك",
        "youtube": "يوتيوب",
        "twitter": "تويتر",
        "x.com": "تويتر",
        "snapchat": "سناب شات",
        "pinterest": "بينتيريست"
    }
    
    for key, name in platforms.items():
        if key in url:
            return name
    return "المنصة"

def is_rate_limited(user_id: int) -> bool:
    """
    التحقق من تجاوز معدل الطلبات المسموح به
    """
    now = time.time()
    last = user_last_request.get(user_id, 0)
    
    if now - last < RATE_LIMIT_SECONDS:
        remaining = int(RATE_LIMIT_SECONDS - (now - last))
        return True, remaining
    
    user_last_request[user_id] = now
    return False, 0

def clean_filename(file_path: str):
    """
    حذف الملف مع معالجة الأخطاء
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"تم حذف الملف: {file_path}")
    except Exception as e:
        logger.error(f"خطأ في حذف الملف: {e}")

# ================ معالج الرسائل الرئيسي ================
@dp.message()
async def handle_message(message: Message):
    # معلومات المستخدم
    user_id = message.from_user.id
    username = message.from_user.username or "مستخدم"
    text = message.text or message.caption or ""
    text = text.strip()
    
    logger.info(f"رسالة جديدة من {username} (ID: {user_id}): {text[:50]}...")
    
    # ===== التحقق من معدل الطلبات =====
    limited, remaining = is_rate_limited(user_id)
    if limited:
        await message.reply(
            f"⏱ تم إرسال طلب مؤخرًا… انتظر {remaining} ثانية."
        )
        return
    
    # ===== التحقق من صحة الرابط =====
    if not is_supported_url(text):
        await message.reply(
            "❌ أرسل رابط فيديو من إحدى المنصات المدعومة:\n\n"
            "📱 انستغرام | تيك توك | فيسبوك\n"
            "▶️ يوتيوب | تويتر | سناب شات | بينتيريست"
        )
        return
    
    # ===== تحديد المنصة =====
    platform = get_platform_name(text)
    
    # ===== إرسال رسالة الانتظار =====
    wait_msg = await message.reply(
        f"⏳ جاري التحميل من {platform}...\n"
        f"🔄 الرجاء الانتظار قليلاً"
    )
    
    # ===== محاولة التحميل مع إعادة المحاولة =====
    file_path = None
    success = False
    
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            logger.info(f"محاولة {attempt + 1} لتحميل: {text}")
            
            # تحديث رسالة الانتظار
            if attempt > 0:
                await wait_msg.edit_text(
                    f"⏳ محاولة {attempt + 1}/{MAX_RETRY_ATTEMPTS}..."
                )
            
            # تحميل الفيديو
            file_path = await asyncio.to_thread(download_video, text)
            
            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # حجم الملف بالميغابايت
                logger.info(f"تم التحميل بنجاح: {file_path} (الحجم: {file_size:.2f} MB)")
                success = True
                break
                
        except Exception as e:
            logger.error(f"خطأ في المحاولة {attempt + 1}: {e}")
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                await asyncio.sleep(RETRY_DELAY)
    
    # ===== حذف رسالة الانتظار =====
    try:
        await wait_msg.delete()
    except:
        pass
    
    # ===== معالجة النتيجة =====
    if success and file_path and os.path.exists(file_path):
        try:
            # محاولة إرسال كفيديو
            video_file = types.FSInputFile(file_path)
            
            # إضافة تأثير الإرسال
            typing_task = asyncio.create_task(
                bot.send_chat_action(message.chat.id, "upload_video")
            )
            
            await message.reply_video(
                video=video_file,
                caption=f"✅ تم التحميل من {platform}\n"
                       f"🎥 بواسطة: @{bot.username}",
                supports_streaming=True
            )
            
            typing_task.cancel()
            logger.info(f"تم إرسال الفيديو للمستخدم {username}")
            
        except TelegramBadRequest:
            # إذا فشل إرسال كفيديو، حاول كمستند
            try:
                doc_file = types.FSInputFile(file_path)
                await message.reply_document(
                    document=doc_file,
                    caption=f"✅ تم التحميل من {platform}\n"
                           f"📎 بواسطة: @{bot.username}"
                )
                logger.info(f"تم إرسال كمستند للمستخدم {username}")
            except Exception as e:
                logger.error(f"فشل إرسال الملف: {e}")
                await message.reply(
                    f"❌ حدث خطأ في إرسال الملف.\n"
                    f"قد يكون حجم الملف كبيراً جداً."
                )
        except Exception as e:
            logger.error(f"خطأ غير متوقع في الإرسال: {e}")
            await message.reply("❌ حدث خطأ غير متوقع في إرسال الملف.")
        
        finally:
            # تنظيف الملف
            clean_filename(file_path)
            
    else:
        # فشل التحميل
        await message.reply(
            "❌ فشل التحميل\n\n"
            "الأسباب المحتملة:\n"
            "• الرابط محمي أو خاص\n"
            "• المنصة غير مدعومة بالكامل\n"
            "• الفيديو طويل جداً\n\n"
            "حاول برابط آخر أو أعد المحاولة لاحقاً."
        )

# ================ معالج الأخطاء ================
@dp.error()
async def error_handler(update: types.Update, exception: Exception):
    """
    معالجة الأخطاء العامة
    """
    logger.error(f"خطأ عام: {exception}", exc_info=True)
    try:
        if update.message:
            await update.message.reply(
                "⚠️ حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى."
            )
    except:
        pass
    return True

# ================ تشغيل البوت ================
async def on_startup():
    """
    دوال يتم تشغيلها عند بدء البوت
    """
    logger.info("=" * 50)
    logger.info("🤖 بوت التحميل يعمل الآن")
    logger.info(f"⚡ توكن البوت: {BOT_TOKEN[:10]}...")
    logger.info(f"⏱ معدل الطلبات: {RATE_LIMIT_SECONDS} ثانية")
    logger.info(f"🔄 عدد المحاولات: {MAX_RETRY_ATTEMPTS}")
    logger.info("=" * 50)

async def on_shutdown():
    """
    دوال يتم تشغيلها عند إيقاف البوت
    """
    logger.info("🤖 تم إيقاف البوت")
    await bot.session.close()

async def main():
    # تشغيل دوال البدء
    await on_startup()
    
    # بدء البوت
    try:
        await dp.start_polling(
            bot,
            skip_updates=True,
            allowed_updates=["message"]
        )
    finally:
        await on_shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")