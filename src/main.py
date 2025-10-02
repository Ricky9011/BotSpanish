import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    load_dotenv()
    token = os.getenv('TOKEN')

    if not token:
        logger.error("❌ Token no encontrado")
        return

    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())

    from src.services.database import DatabaseService
    DatabaseService.initialize()

    # Registrar routers normales
    from src.handlers.commands import router as commands_router
    from src.handlers.curiosities import router as curiosities_router
    from src.handlers.exercises import router as exercises_router
    from src.handlers.reto import router as reto_router
    from src.handlers.progress import router as progress_router
    from src.handlers.nivel import router as nivel_router
    from src.handlers.feedback import router as feedback_router
    from src.handlers.admin import router as admin_router
    from src.handlers.callbacks import router as callbacks_router


    dp.include_router(commands_router)
    dp.include_router(curiosities_router)  # ✅ PRIMERO - Maneja show_curiosity
    dp.include_router(exercises_router)
    dp.include_router(reto_router)
    dp.include_router(progress_router)
    dp.include_router(nivel_router)
    dp.include_router(feedback_router)
    dp.include_router(admin_router)
    dp.include_router(callbacks_router)  # ✅ DESPUÉS - No maneja show_curiosity




    # Handler específico para respuestas numéricas (por si hay conflicto)
    @dp.message(F.text.regexp(r"^\d+$"))
    async def numeric_fallback(message: Message):
        logger.info(f"Respuesta numérica recibida: {message.text}")
        # Este handler actuará como fallback si los routers no capturan la respuesta

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🚀 Bot híbrido iniciado")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    @dp.message()
    async def unhandled_message(message: Message):
        logger.info(f"Mensaje no manejado: {message.text}")

if __name__ == "__main__":
    asyncio.run(main())