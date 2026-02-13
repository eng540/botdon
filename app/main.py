import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from downloader import download_video

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: Message):
    url = message.text.strip()

    await message.reply("جاري التحميل ⏳")

    file_path = None

    # إعادة المحاولة الذكية
    for attempt in range(3):
        try:
            file_path = await asyncio.to_thread(download_video, url)
            if file_path:
                break
        except Exception:
            await asyncio.sleep(5)

    if file_path and os.path.exists(file_path):
        try:
            await message.reply_video(types.FSInputFile(file_path))
        except:
            await message.reply_document(types.FSInputFile(file_path))

        os.remove(file_path)
    else:
        await message.reply("فشل التحميل ❌ الرابط محمي أو غير مدعوم")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())