from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.services.user_service import UserService
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

class LevelStates(StatesGroup):
    waiting_level = State()

def level_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Principiante"), KeyboardButton(text="Intermedio")],
            [KeyboardButton(text="Avanzado")]
        ],
        resize_keyboard=True
    )
    return kb

@router.message(Command("nivel"))
@router.message(F.text == "Cambiar de nivel")
async def cmd_level(message: Message, state: FSMContext):
    await message.answer(
        "📊 Selecciona tu nuevo nivel:",
        reply_markup=level_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(LevelStates.waiting_level)

@router.message(LevelStates.waiting_level)
async def set_level(message: Message, state: FSMContext):
    level = message.text.lower()
    valid_levels = ["principiante", "intermedio", "avanzado"]
    user_id = message.from_user.id

    if level in valid_levels:
        UserService.set_user_level(user_id, level)
        await message.answer(
            f"✅ Nivel cambiado a *{level}*.",
            parse_mode="Markdown",
            reply_markup=None
        )
    else:
        await message.answer(
            "❌ Nivel no válido. Elige: Principiante, Intermedio, Avanzado.",
            reply_markup=level_keyboard(),
            parse_mode="Markdown"
        )
    await state.clear()