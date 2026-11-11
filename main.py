import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ==========================================
BOT_TOKEN = "9083681390:AAE_OGDKvkKP-kfv0FPz_-yfxZ1 aQ00fWfk"
ADMIN_ID = 8863524976 
# ==========================================

DB_NAME = "movies.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                code TEXT PRIMARY KEY,
                title TEXT,
                file_id TEXT
            )
        """)
        await db.commit()

async def add_movie(code: str, title: str, file_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO movies (code, title, file_id) VALUES (?, ?, ?)",
            (code, title, file_id)
        )
        await db.commit()

async def get_movie(code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT title, file_id FROM movies WHERE code = ?", (code,)) as cursor:
            return await cursor.fetchone()

class AddMovieState(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()
    waiting_for_title = State()

dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Salom! Kino botimizga xush kelibsiz.\n\n"
        "🎬 Kino olish uchun kino kodini yuboring (Masalan: 101)."
    )

@dp.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat admin uchun!")
        return
    
    await state.set_state(AddMovieState.waiting_for_video)
    await message.answer("📹 Kino videosini yuboring:")

@dp.message(AddMovieState.waiting_for_video, F.video)
async def process_video(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovieState.waiting_for_code)
    await message.answer("🔢 Endi bu kino uchun kod kiriting (masalan: 101):")

@dp.message(AddMovieState.waiting_for_code, F.text)
async def process_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text.strip())
    await state.set_state(AddMovieState.waiting_for_title)
    await message.answer("✏️ Kino nomini kiriting:")

@dp.message(AddMovieState.waiting_for_title, F.text)
async def process_title(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = data["code"]
    file_id = data["file_id"]
    title = message.text.strip()

    await add_movie(code, title, file_id)
    await state.clear()
    await message.answer(f"✅ Kino muvaffaqiyatli saqlandi!\n\n📌 Nomi: {title}\n🔑 Kodi: `{code}`")

@dp.message(F.text)
async def get_movie_by_code(message: types.Message):
    code = message.text.strip()
    movie = await get_movie(code)

    if movie:
        title, file_id = movie
        await message.answer_video(video=file_id, caption=f"🎬 **{title}**\n🔑 Kodi: `{code}`")
    else:
        await message.answer("❌ Bu kod bilan kino topilmadi.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
