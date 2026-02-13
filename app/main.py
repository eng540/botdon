import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InputFile
from downloader import download_video
from config import RATE_LIMIT_SECONDS

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_last_request = {}

def is_video_url(text: str) -> bool:
    domains = ["instagram.com", "tiktok.com", "facebook.com"]
    return any(d in text for d in domains)

def rate_limited(user_id: int) -> bool:
    import time
    now = time.time()
    last = user_last_request.get(user_id, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    user_last_request[user_id] = now
    return False

@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    text = (message.text or "").strip()

    if rate_limited(user_id):
        await message.reply("تم إرسال طلب مؤخرًا… انتظر قليلًا ⏱")
        return

    if not is_video_url(text):
        await message.reply("أرسل رابط فيديو من Instagram أو TikTok أو Facebook.")
        return

    await message.reply("جاري التحميل ⏳")

    try:
        path = await asyncio.to_thread(download_video, text)
        video = InputFile(path)
        await message.answer_video(video)
        try:
            os.remove(path)
        except Exception:
            pass
    except Exception as e:
        await message.reply("فشل التحميل ❌")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)