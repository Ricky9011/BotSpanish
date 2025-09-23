import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from src.services.user_service import UserService
from src.keyboards.main_menu import MainMenuKeyboard  # ✅ IMPORT CORRECTO
logger = logging.getLogger(__name__)
router = Router(name="logros")

@router.message(Command("logros"))
async def cmd_logros(message: Message):
    user_id = message.from_user.id
    achievements = UserService.get_achievements(user_id)
    # Lógica del antiguo `logros` (lista de logros)
    await message.answer("Tus logros: [lista]")