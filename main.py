import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers import router

logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация БД
    init_db()
    
    # Бот
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🚀 Бот TJ Security AI запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
