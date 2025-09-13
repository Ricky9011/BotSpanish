from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("invitar"))
async def cmd_invitar(message: Message):
    # Lógica del antiguo `invitar` (enlace de invitación)
    await message.answer("Invita amigos: [enlace]")