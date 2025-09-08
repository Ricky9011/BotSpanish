import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from .handlers import commands, exercises, feedback, progress, admin, curiosities
from .services.database import DatabaseService
from dotenv import load_dotenv

load_dotenv()

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def main():
    TOKEN = os.getenv("TOKEN")
    bot = Bot(token=os.getenv('TOKEN'))
    dp = Dispatcher(storage=MemoryStorage())

    # Registrar routers
    dp.include_router(commands.router)
    dp.include_router(exercises.router)
    dp.include_router(feedback.router)
    dp.include_router(progress.router)
    dp.include_router(admin.router)
    dp.include_router(curiosities.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
