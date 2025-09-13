from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

from src.handlers.feedback import cmd_opinion
from src.services.user_service import UserService
from src.keyboards.main_menu import MainMenuKeyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    # Registrar usuario
    UserService.register_user(user_id, username)

    # Mensaje de bienvenida
    welcome_text = (
        f"👋 ¡Hola {message.from_user.first_name}! "
        "Bienvenido a tu práctica diaria de español.\n\n"
        "Usa /ayuda para ver los comandos disponibles."
    )

    # Enviar mensaje con teclado principal
    await message.answer(
        welcome_text,
        reply_markup=await MainMenuKeyboard.build()
    )


@router.message(Command("ayuda"))
async def cmd_help(message: Message):
    help_text = """
    📖 **Comandos Disponibles:**
    /ejercicio - Ejercicio diario personalizado
    /reto - ¡Compite en el desafío semanal!
    /progreso - Tu avance y estadísticas
    /nivel - Cambiar nivel (principiante/intermedio/avanzado)
    /invitar - Invita amigos y gana recompensas
    /premium - Información sobre contenido exclusivo
    /opinion - Enviar sugerencias o reportar errores
    /logros - Ver tus logros obtenidos
    """
    await message.answer(help_text)


# Add at the end of commands.py
__all__ = ['cmd_start', 'cmd_help']
