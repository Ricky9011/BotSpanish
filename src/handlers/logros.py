from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from src.services.user_service import UserService

router = Router()

@router.message(Command("logros"))
async def cmd_logros(message: Message):
    user_id = message.from_user.id
    achievements = UserService.get_achievements(user_id)
    # Lógica del antiguo `logros` (lista de logros)
    await message.answer("Tus logros: [lista]")