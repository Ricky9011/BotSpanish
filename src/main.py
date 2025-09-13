import asyncio
import logging
import os
import aiogram
import dotenv
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.handlers import feedback, progress, admin, commands, curiosities, exercises, invitar, logros, nivel, settings, reto, premium
from src.services.database import DatabaseService

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cargar .env explícitamente
env_path = "/home/ricky/PycharmProjects/BotSpanish/.env"
if not os.path.exists(env_path):
    logging.error(f".env file not found at: {env_path}")
    raise FileNotFoundError(f".env file not found at: {env_path}")
dotenv.load_dotenv(env_path)
logging.info(f"Loaded .env from: {dotenv.find_dotenv()}")
logging.info(f"DB_HOST: {os.getenv('DB_HOST')}")
logging.info(f"DB_PORT: {os.getenv('DB_PORT')}")
logging.info(f"DB_NAME: {os.getenv('DB_NAME')}")
logging.info(f"DB_USER: {os.getenv('DB_USER')}")
logging.info(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')[:4] if os.getenv('DB_PASSWORD') else None}...")
logging.info(f"TOKEN: {os.getenv('TOKEN')[:4] if os.getenv('TOKEN') else None}...")

# Inicializar el bot
bot = aiogram.Bot(token=os.getenv('TOKEN'))

# Inicializar la base de datos
DatabaseService.initialize()

# Función para enviar recordatorios
async def enviar_recordatorio():
    try:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()
            for user in users:
                try:
                    await bot.send_message(chat_id=user[0], text="⏰ ¡No olvides practicar hoy! Usa /ejercicio para tu práctica diaria.")
                except Exception as e:
                    logger.error(f"Error enviando recordatorio a {user[0]}: {e}")
    except Exception as e:
        logger.error(f"Error en recordatorio: {e}")

async def main():
    dp = aiogram.Dispatcher(storage=MemoryStorage())
    dp.include_router(commands.router)
    dp.include_router(exercises.router)
    dp.include_router(feedback.router)
    dp.include_router(progress.router)
    dp.include_router(admin.router)
    dp.include_router(curiosities.router)
    dp.include_router(nivel.router)
    dp.include_router(logros.router)
    dp.include_router(invitar.router)
    dp.include_router(reto.router)


    # Configurar el scheduler
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(enviar_recordatorio, 'cron', hour=9, minute=0)
    scheduler.start()  # Iniciar el scheduler dentro del bucle de eventos

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

    # Asegurar que el scheduler se detenga al cerrar el bot
    scheduler.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")