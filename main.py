import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import init_db
from handlers.admin import admin_router
from handlers.user import user_router
from handlers.game import game_router

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Register modular routers
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(game_router)

    print("Keno Bot started successfully.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
