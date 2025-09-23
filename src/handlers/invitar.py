import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from src.services.user_service import UserService
from src.keyboards.main_menu import MainMenuKeyboard  # ✅ IMPORT CORRECTO
logger = logging.getLogger(__name__)
router = Router(name="invitar")

@router.message(Command("invitar"))
async def cmd_invitar(message: Message):
    # Lógica del antiguo `invitar` (enlace de invitación)
    await message.answer("Invita amigos: [enlace]")