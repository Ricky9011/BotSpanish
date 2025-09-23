import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command
from src.services.database import DatabaseService
from src.keyboards.main_menu import MainMenuKeyboard  # ✅ IMPORT CORRECTO
from src.utils import sanitize_text

logger = logging.getLogger(__name__)
router = Router(name="curiosities")


@router.message(Command("curiosidad"))
@router.message(F.text == "📚 Curiosidad")
async def cmd_curiosidad(message: Message, state: FSMContext):
    await state.clear()
    curiosity = DatabaseService.get_random_curiosity()

    if not curiosity:
        await message.answer("No hay curiosidades disponibles en este momento.")
        return

    message_text = (
        f"🧠*Curiosidad del español ({curiosity.texto}):*\n\n"
        f"{sanitize_text(curiosity.texto)}"
    )

    await message.answer(message_text, parse_mode="Markdown")
    await message.answer(
        "Puedes ver más curiosidades usando /curiosidad o el botón de abajo.",
        reply_markup=MainMenuKeyboard().main_menu(),
        parse_mode="Markdown"
    )
__all__ = ['cmd_curiosidad']
