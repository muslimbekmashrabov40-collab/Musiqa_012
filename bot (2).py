import os
import glob
import asyncio
import shutil
import tempfile

import yt_dlp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

import static_ffmpeg
static_ffmpeg.add_paths()  # ffmpeg ni avtomatik yuklab, ulab beradi

TOKEN = os.getenv("BOT_TOKEN")  # BotFather bergan token
bot = Bot(TOKEN)
dp = Dispatcher()

MAX_MB = 48  # Telegram bot uchun fayl limiti ~50 MB


def download(url: str, audio: bool, folder: str) -> str:
    opts = {
        "outtmpl": f"{folder}/%(title).60s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "max_filesize": MAX_MB * 1024 * 1024,
    }
    if audio:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        opts["format"] = "best[ext=mp4][filesize<48M]/best[ext=mp4][filesize_approx<48M]/worst[ext=mp4]/worst"

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    files = glob.glob(f"{folder}/*")
    if not files:
        raise RuntimeError("Fayl topilmadi")
    return files[0]


@dp.message(CommandStart())
async def start(m: Message):
    await m.answer(
        "👋 Salom! Men *Mashrabov* botiman.\n"
        "YouTube, Instagram, TikTok va boshqa havolalarni yuboring — "
        "video yoki MP3 qilib yuklab beraman.",
        parse_mode="Markdown",
    )


@dp.message(F.text.regexp(r"https?://"))
async def got_link(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🎬 Video", callback_data="v"),
        InlineKeyboardButton(text="🎵 MP3", callback_data="a"),
    ]])
    await m.reply("Qaysi formatda yuklay?", reply_markup=kb)


@dp.callback_query(F.data.in_({"v", "a"}))
async def choose(c: CallbackQuery):
    url = c.message.reply_to_message.text.strip()
    audio = c.data == "a"
    await c.message.edit_text("⏳ Yuklanmoqda...")

    folder = tempfile.mkdtemp()
    try:
        path = await asyncio.to_thread(download, url, audio, folder)
        file = FSInputFile(path)
        if audio:
            await c.message.answer_audio(file, caption="@Muslimjon890")
        else:
            await c.message.answer_video(file, caption="@Muslimjon890")
        await c.message.delete()
    except Exception:
        await c.message.edit_text(
            "❌ Yuklab boʻlmadi. Havolani tekshiring yoki fayl juda katta (50 MB dan oshiq)."
        )
    finally:
        shutil.rmtree(folder, ignore_errors=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
