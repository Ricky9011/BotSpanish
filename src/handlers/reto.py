# Crea un nuevo archivo challenge.py en la carpeta handlers
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from src.services.database import DatabaseService
from src.services.user_service import UserService

router = Router()


@router.message(Command("reto"))
@router.callback_query(F.data == "daily_challenge")
async def daily_challenge(message: Message | CallbackQuery):
    if isinstance(message, CallbackQuery):
        message = message.message

    user_id = message.from_user.id
    # Lógica para el reto diario Por ejemplo, un ejercicio especial o un conjunto de ejercicios, aqui integrare
    # despues ejercicios de nivel dificil a la bd.

    # Obtener un ejercicio especial para el reto
    with DatabaseService.get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM ejercicios 
            WHERE nivel = 'avanzado' 
            ORDER BY RANDOM() 
            LIMIT 1
        """)
        exercise = cursor.fetchone()

    if exercise:
        # Formatear y enviar el ejercicio
        message_text = f"🏆 *Reto Diario*\n\n{exercise['pregunta']}\n\n"
        for idx, opcion in enumerate(exercise['opciones']):
            message_text += f"{idx + 1}. {opcion}\n"

        await message.answer(message_text, parse_mode="Markdown")
    else:
        await message.answer("❌ No hay retos disponibles en este momento.")