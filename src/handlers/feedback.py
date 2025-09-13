from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.services.database import DatabaseService

router = Router()


class FeedbackStates(StatesGroup):
    waiting_feedback = State()


@router.message(Command("opinion"))
async def cmd_opinion(message: Message, state: FSMContext):
    await message.answer("📝 Por favor, escribe tu opinión, sugerencia o reporte de error.", parse_mode="Markdown")
    await state.set_state(FeedbackStates.waiting_feedback)


@router.message(FeedbackStates.waiting_feedback)
async def receive_opinion(message: Message, state: FSMContext):
    user_id = message.from_user.id
    feedback_text = message.text
    try:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO feedback (user_id, message)
                VALUES (%s, %s)
            """, (user_id, feedback_text))
        await message.answer("✅ ¡Gracias por tu opinión! Tu feedback nos ayuda a mejorar.", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"⚠️ Error al guardar tu opinión: {e}", parse_mode="Markdown")
    await state.clear()


@router.message(F.text == "💬 Enviar Opinión")
async def cmd_feedback_button(message: Message, state: FSMContext):
    await cmd_opinion(message, state)
    # Add at the end of feedback.py
    __all__ = ['cmd_feedback_button']
