from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from telegram import ReplyKeyboardMarkup
from src.keyboards.main_menu import MainMenuKeyboard
from ..services.database import DatabaseService

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, db: DatabaseService):
    # Lógica migrada de tu función start original
    await message.answer(
        f"👋 ¡Hola {message.from_user.first_name}!",
        reply_markup=await MainMenuKeyboard.build()
    )
