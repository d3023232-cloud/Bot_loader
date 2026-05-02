# Файл: uploader_bot.py (для папки бота-загрузчика)
import asyncio
import sqlite3
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ==============================================
# ⚙️ НАСТРОЙКИ
# ==============================================
BOT_TOKEN = "8587181435:AAHK2D6gV8wOamWSleO-amCC9BmIrLb0nNw"  # <-- ВАЖНО! Токен от второго бота
ADMIN_IDS = [5975768284, 8319217707, 6403805365]
# ==============================================

# ========== ИНИЦИАЛИЗАЦИЯ ==========
logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# ========== БД ==========
DATABASE_PATH = "/app/shared/cinema.db"  # Путь к базе в томе

def get_db_connection():
    """Создает соединение с БД с таймаутом для многопоточного доступа."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, year TEXT, rating_kp REAL, rating_imdb REAL,
        country TEXT, genres TEXT, keywords TEXT, description TEXT,
        video_file_id TEXT, created_at TIMESTAMP
    )""")
    conn.commit()
    conn.close()

# ========== СОСТОЯНИЯ ДЛЯ ЗАГРУЗКИ ==========
class UploadStates(StatesGroup):
    waiting_for_video = State()
    waiting_for_title = State()
    waiting_for_year = State()
    waiting_for_country = State()
    waiting_for_genres = State()
    waiting_for_keywords = State()
    waiting_for_rating_kp = State()
    waiting_for_rating_imdb = State()
    waiting_for_description = State()

# ========== КОМАНДА /start ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Доступ запрещён.")
        return
    
    await message.answer(
        "🎬 *Бот-загрузчик фильмов*\n\n"
        "Отправь мне видео, чтобы начать процесс добавления.",
        parse_mode=ParseMode.MARKDOWN
    )

# ========== ШАГ 1: Получение видео ==========
@dp.message(UploadStates.waiting_for_video)
async def process_video(message: types.Message, state: FSMContext):
    if not message.video:
        await message.answer("❌ Пожалуйста, отправьте видео файлом.")
        return
    
    await state.update_data(video_file_id=message.video.file_id)
    await message.answer("✅ Видео получено! Теперь введи *название* фильма:")
    await state.set_state(UploadStates.waiting_for_title)

# ========== ШАГ 2: Название ==========
@dp.message(UploadStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("📅 Введи *год* выпуска (например, 2023):")
    await state.set_state(UploadStates.waiting_for_year)

# ========== ШАГ 3: Год ==========
@dp.message(UploadStates.waiting_for_year)
async def process_year(message: types.Message, state: FSMContext):
    year = message.text.strip()
    if not year.isdigit() or len(year) != 4:
        await message.answer("❌ Введи корректный год (4 цифры).")
        return
    await state.update_data(year=year)
    await message.answer("🌍 Введи *страну* производства (например, США, Россия):")
    await state.set_state(UploadStates.waiting_for_country)

# ========== ШАГ 4: Страна ==========
@dp.message(UploadStates.waiting_for_country)
async def process_country(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text.strip())
    await message.answer("🎭 Введи *жанры* через запятую (например, драма, комедия):")
    await state.set_state(UploadStates.waiting_for_genres)

# ========== ШАГ 5: Жанры ==========
@dp.message(UploadStates.waiting_for_genres)
async def process_genres(message: types.Message, state: FSMContext):
    await state.update_data(genres=message.text.strip())
    await message.answer("🔑 Введи *ключевые слова* через запятую (по ним фильм будут искать):")
    await state.set_state(UploadStates.waiting_for_keywords)

# ========== ШАГ 6: Ключевые слова ==========
@dp.message(UploadStates.waiting_for_keywords)
async def process_keywords(message: types.Message, state: FSMContext):
    await state.update_data(keywords=message.text.strip().lower())
    await message.answer("⭐ Введи *рейтинг Кинопоиска* (например, 7.5 или 0 если нет):")
    await state.set_state(UploadStates.waiting_for_rating_kp)

# ========== ШАГ 7: Рейтинг Кинопоиска ==========
@dp.message(UploadStates.waiting_for_rating_kp)
async def process_rating_kp(message: types.Message, state: FSMContext):
    try:
        val = float(message.text.strip().replace(',', '.'))
        await state.update_data(rating_kp=val if val > 0 else None)
    except ValueError:
        await state.update_data(rating_kp=None)
    await message.answer("🎬 Введи *рейтинг IMDb* (например, 8.2 или 0 если нет):")
    await state.set_state(UploadStates.waiting_for_rating_imdb)

# ========== ШАГ 8: Рейтинг IMDb ==========
@dp.message(UploadStates.waiting_for_rating_imdb)
async def process_rating_imdb(message: types.Message, state: FSMContext):
    try:
        val = float(message.text.strip().replace(',', '.'))
        await state.update_data(rating_imdb=val if val > 0 else None)
    except ValueError:
        await state.update_data(rating_imdb=None)
    await message.answer(
        "📝 *Шаг 9/9:* Введи описание фильма.\n\n"
        "*Совет:* Опиши краткий сюжет, главных героев, интересные детали. Это увидит пользователь.",
        parse_mode=ParseMode.MARKDOWN
    )
    await state.set_state(UploadStates.waiting_for_description)

# ========== ШАГ 9: Описание и сохранение ==========
@dp.message(UploadStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    data = await state.update_data(description=message.text.strip())
    
    # Сохранение в БД
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO movies (title, year, rating_kp, rating_imdb, country, genres, keywords, description, video_file_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['title'], data['year'], data['rating_kp'], data['rating_imdb'],
        data['country'], data['genres'], data['keywords'], data['description'],
        data['video_file_id'], datetime.now().isoformat()
    ))
    conn.commit()
    movie_id = c.lastrowid
    conn.close()
    
    await message.answer(
        f"✅ *Фильм успешно добавлен!*\n\n"
        f"🎬 Название: *{data['title']}*\n"
        f"🆔 ID: `{movie_id}`\n"
        f"🔑 Ключевые слова: `{data['keywords']}`\n\n"
        f"Теперь он доступен для поиска в основном боте.",
        parse_mode=ParseMode.MARKDOWN
    )
    await state.clear()

# ========== ЗАПУСК ==========
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
