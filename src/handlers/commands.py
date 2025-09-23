# handlers/commands.py - CON IMPORT CORRECTO
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from src.services.user_service import UserService
from src.keyboards.main_menu import MainMenuKeyboard  # ✅ IMPORT CORRECTO
logger = logging.getLogger(__name__)
router = Router(name="commands")

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

    # Enviar mensaje con teclado principal - ✅ FORMA CORRECTA
    await message.answer(
        welcome_text,
        reply_markup=MainMenuKeyboard.main_menu()  # ✅ LLAMADA CORRECTA
    )

@router.message(Command("ayuda"))
async def cmd_help(message: Message):
    help_text = """
📖 **Comandos Disponibles:**

**📝 Práctica:**
/ejercicio - Ejercicio personalizado según tu nivel
/reto - Reto diario de nivel superior

**📊 Progreso:**
/progreso - Tu avance y estadísticas
/logros - Logros obtenidos

**⚙️ Configuración:**
/nivel - Cambiar nivel (principiante/intermedio/avanzado)
/opinion - Enviar sugerencias o reportar errores

**🎮 Extras:**
/curiosidad - Curiosidades del español
/invitar - Invita amigos y gana recompensas
"""
    await message.answer(help_text)

@router.message(F.text == "Volver al menú")
async def back_to_menu(message: Message):
    await message.answer(
        "🏠 Volviendo al menú principal...",
        reply_markup=MainMenuKeyboard.main_menu()  # ✅ Misma llamada
    )