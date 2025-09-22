from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.services.user_service import UserService
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from src.keyboards.main_menu import MainMenuKeyboard
import pytest

# Create a router instance to handle commands and messages
router = Router()

# Define a state group for managing user levels
class LevelStates(StatesGroup):
    # State for waiting for the user to select a level
    waiting_level = State()

# Function to create a keyboard for level selection
def level_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a ReplyKeyboardMarkup for selecting user levels.

    Returns:
        ReplyKeyboardMarkup: A keyboard with buttons for "Principiante", "Intermedio", and "Avanzado".
    """
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Principiante"), KeyboardButton(text="Intermedio")],
            [KeyboardButton(text="Avanzado")]
        ],
        resize_keyboard=True
    )
    return kb

# Command handler for "/nivel" or "Cambiar de nivel"
@router.message(Command("nivel"))
@router.message(F.text == "Cambiar de nivel")
async def cmd_level(message: Message, state: FSMContext):
    """
    Handles the "/nivel" command or "Cambiar de nivel" message.

    Args:
        message (Message): The incoming message object.
        state (FSMContext): The finite state machine context for managing user states.

    Sends a message with a keyboard for level selection and sets the state to waiting_level.
    """
    await message.answer(
        "📊 Puedes seleccionar un nivel directamente o usar el menú:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Principiante"), KeyboardButton(text="Intermedio")],
                [KeyboardButton(text="Avanzado"), KeyboardButton(text="Volver al menú")]
            ],
            resize_keyboard=True
        ),
        parse_mode="Markdown"
    )
    await state.set_state(LevelStates.waiting_level)

# Handler for processing the selected level
@router.message(LevelStates.waiting_level)
async def set_level(message: Message, state: FSMContext):
    """
    Handles the user's level selection.

    Args:
        message (Message): The incoming message object containing the user's level choice.
        state (FSMContext): The finite state machine context for managing user states.

    Validates the selected level, updates the user's level in the database, and sends a confirmation message.
    If the level is invalid, prompts the user to select a valid level.
    """
    level = message.text.lower()
    valid_levels = ["principiante", "intermedio", "avanzado"]
    user_id = message.from_user.id

    if level in valid_levels:
        # Update the user's level in the database
        UserService.set_user_level(user_id, level)
        await message.answer(
            f"✅ Nivel cambiado a *{level}*.",
            parse_mode="Markdown",
            reply_markup=await MainMenuKeyboard.build()
        )
    else:
        # Prompt the user to select a valid level
        await message.answer(
            "❌ Nivel no válido. Elige: Principiante, Intermedio, Avanzado.",
            reply_markup=level_keyboard(),
            parse_mode="Markdown"
        )
    # Clear the state after processing the level
    await state.clear()
