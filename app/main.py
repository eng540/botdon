import os
import asyncio
import time
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from downloader import download_video, cleanup_old_files

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

RATE_LIMIT = 10
user_last = {}

logging.basicConfig(level=logging.INFO)

def is_limited(user_id):
    now = time.time()
    last = user_last.get(user_id, 0)
    if now - last < RATE_LIMIT:
        return True, int(RATE_LIMIT - (now - last))
    user_last[user_id] = now
    return False, 0

def is_url(text):
    if not text:
        return False
    domains = [
        "youtube", "youtu.be",
        "facebook", "instagram",
        "tiktok", "twitter", "x.com"
    ]
    return any(d in text.lower() for d in domains)

@dp.message()
async def handler(message: Message):
    text = message.text or ""
    text = text.strip()

    limited, remain = is_limited(message.from_user.id)
    if limited:
        await message.reply(f"انتظر {remain} ثانية ⏱")
        return

    if not is_url(text):
        await message.reply("أرسل رابط فيديو صحيح")
        return

    wait = await message.reply("جاري التحميل ⏳")

    file_path = await asyncio.to_thread(download_video, text)

    try:
        await wait.delete()
    except:
        pass

    if not file_path:
        await message.reply("فشل التحميل ❌")
        return

    try:
        await message.reply_video(types.FSInputFile(file_path))
    except TelegramBadRequest:
        await message.reply_document(types.FSInputFile(file_path))
    except:
        await message.reply("فشل إرسال الملف ❌")

    try:
        os.remove(file_path)
    except:
        pass

async def main():
    cleanup_old_files()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())