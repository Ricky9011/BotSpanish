from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from src.services.database import DatabaseService
from src.utils.helpers import sanitize_text

router = Router()


@router.message(Command("curiosidad"))
@router.message(F.text == "📚 Curiosidad")
async def cmd_curiosidad(message: Message):
    curiosity = DatabaseService.get_random_curiosity()

    if not curiosity:
        await message.answer("No hay curiosidades disponibles en este momento.")
        return

    message_text = (
        f"🧠*Curiosidad del español ({curiosity.texto}):*\n\n"
        f"{sanitize_text(curiosity.texto)}"
    )

    await message.answer(message_text, parse_mode="Markdown")