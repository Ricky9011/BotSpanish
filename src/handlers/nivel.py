import logging
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from src.services.user_service import UserService
from src.keyboards.main_menu import MainMenuKeyboard

logger = logging.getLogger(__name__)

router = Router(name="nivel")

class LevelStates(StatesGroup):
    waiting_level = State()

def level_keyboard() -> ReplyKeyboardMarkup:
    """Teclado para selección de nivel"""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Principiante"), KeyboardButton(text="Intermedio")],
            [KeyboardButton(text="Avanzado"), KeyboardButton(text="🏠 Menú Principal")]
        ],
        resize_keyboard=True
    )
    return kb

# 🔥 CORRECCIÓN: Cambiar el filtro para que coincida con el texto del botón
@router.message(Command("nivel"))
@router.message(F.text == "⚙️ Cambiar Nivel")  # ✅ Texto exacto del botón
async def cmd_level(message: Message, state: FSMContext):
    """
    Handles the "/nivel" command or "⚙️ Cambiar Nivel" message.
    """
    await message.answer(
        "🎯 *Selecciona tu nivel de español:*\n\n"
        "• **Principiante**: Conceptos básicos\n"
        "• **Intermedio**: Frases y gramática\n"  
        "• **Avanzado**: Expresiones complejas",
        reply_markup=level_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(LevelStates.waiting_level)

@router.message(LevelStates.waiting_level)
async def set_level(message: Message, state: FSMContext):
    """Maneja la selección de nivel"""
    level = message.text.lower()
    valid_levels = ["principiante", "intermedio", "avanzado", "menú principal"]
    user_id = message.from_user.id

    if level in valid_levels:
        if level == "menú principal":
            # Volver al menú principal
            await message.answer(
                "🏠 Volviendo al menú principal...",
                reply_markup=MainMenuKeyboard.main_menu()
            )
        else:
            # Actualizar nivel del usuario
            UserService.set_user_level(user_id, level)
            await message.answer(
                f"✅ *Nivel actualizado a: {level.capitalize()}*",
                parse_mode="Markdown",
                reply_markup=MainMenuKeyboard.main_menu()
            )
    else:
        # Nivel no válido
        await message.answer(
            "❌ Nivel no válido. Por favor selecciona:\n\n"
            "• Principiante\n• Intermedio\n• Avanzado\n• Menú Principal",
            reply_markup=level_keyboard()
        )
        return  # No limpiar el estado para permitir reintento

    await state.clear()