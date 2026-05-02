# uploader_bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = "ТОКЕН_ВТОРОГО_БОТА"          # замените
ADMIN_IDS = [5975768248, 8319217707, 6403805365]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Доступ запрещён")
        return
    await message.answer("Отправь мне видео, и я пришлю его file_id.")

@dp.message(lambda msg: msg.video is not None)
async def get_file_id(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    file_id = message.video.file_id
    await message.answer(f"`{file_id}`", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
