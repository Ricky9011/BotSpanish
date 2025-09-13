from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("premium"))
async def cmd_premium(message: Message):
    # Lógica del antiguo `premium` (contenido exclusivo)
    await message.answer("Información sobre premium: [detalles]")