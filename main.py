import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from handlers import register_handlers
from admin import register_admin_handlers

# .env fayldan o'qish
load_dotenv()

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot va Dispatcher yaratish
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def main():
    """Botni ishga tushirish"""
    try:
        # Handlerlarni ro'yxatdan o'tkazish
        register_handlers(dp)
        register_admin_handlers(dp)
        
        logger.info("Bot ishga tushdi!")
        
        # Botni polling rejimida ishga tushirish
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Bot ishga tushirishda xatolik: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi")
