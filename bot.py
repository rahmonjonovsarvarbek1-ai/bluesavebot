import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from yt_dlp import YoutubeDL
from concurrent.futures import ThreadPoolExecutor

# --- SOZLAMALAR ---
TOKEN = "8487764182:AAEkK3XxhlGOtr6oe5QlxrGkLZ15OS-Tj0o"
ADMIN_ID = 8487764182  # O'z ID-ingizni bu yerda tekshirib oling
DOWNLOAD_PATH = "downloads/"
USERS_FILE = "users.txt"

# FFmpeg-ning aniq manzili (Siz yuborgan manzil asosida)
FFMPEG_EXE = r"C:\Users\ISHONCH\Desktop\bluesavebot\ffmpeg.exe"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()
thread_pool = ThreadPoolExecutor(max_workers=20)

# --- USER DATABASE LOGIC ---
def save_user(user_id):
    if not os.path.exists(USERS_FILE):
        open(USERS_FILE, "w").close()
    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{user_id}\n")

def get_users_count():
    if not os.path.exists(USERS_FILE): return 0
    with open(USERS_FILE, "r") as f:
        return len(f.read().splitlines())

# --- LIFESPAN (FastAPI + Bot) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 BLUESAVE ELITE v3.1 ISHGA TUSHDI")
    polling_task = asyncio.create_task(dp.start_polling(bot))
    yield
    polling_task.cancel()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

# --- YUKLASH MOTORINI OPTIMALLASHTIRISH ---
YDL_OPTIONS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4/best',
    'outtmpl': f'{DOWNLOAD_PATH}%(id)s.%(ext)s',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'ffmpeg_location': FFMPEG_EXE # FFmpeg manzilini ko'rsatdik
}

async def download_media(url):
    loop = asyncio.get_running_loop()
    try:
        with YoutubeDL(YDL_OPTIONS) as ydl:
            # Yuklashni thread pool-da bajarish (Botni qotirmaslik uchun)
            info = await loop.run_in_executor(thread_pool, lambda: ydl.extract_info(url, download=True))
            return ydl.prepare_filename(info)
    except Exception as e:
        logger.error(f"Download Error: {e}")
        return None

# --- TELEGRAM HANDLERS ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        f"🌟 **Salom {message.from_user.first_name}!**\n\n"
        "Men **BLUESAVE PRO** yuklovchisiman.\n"
        "Instagram, YouTube va Pinterest linklarini yuboring!",
        parse_mode="Markdown"
    )

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        await message.answer(f"📊 **Bot Statistikasi:**\n\n👤 Foydalanuvchilar: {count}")
    else:
        await message.answer("❌ Bu buyruq faqat admin uchun.")

@dp.message(F.text.contains("http"))
async def handle_link(message: types.Message):
    url = message.text
    status = await message.answer("🔄 **Tayyorlanmoqda...**")
    
    file_path = await download_media(url)
    
    if file_path and os.path.exists(file_path):
        await status.edit_text("📤 **Yuborilmoqda...**")
        file_input = types.FSInputFile(file_path)
        
        try:
            if file_path.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                await message.answer_photo(photo=file_input, caption="✅ Media yuklandi")
            else:
                await message.answer_video(video=file_input, caption="✅ @BlueSaveBot orqali yuklandi")
        except Exception as e:
            logger.error(f"Send Error: {e}")
            await message.answer_document(document=file_input, caption="📁 Media fayli")
        
        os.remove(file_path)
        await status.delete()
    else:
        await status.edit_text("❌ Yuklab bo'lmadi. Linkni tekshiring yoki serverda xatolik.")

# --- FASTAPI ROUTE ---
@app.get("/")
async def root():
    return {"status": "running"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001) # 8000 o'rniga 8001