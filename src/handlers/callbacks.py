# handlers/callbacks.py - EXPANDIDO
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from src.handlers.reto import daily_challenge

router = Router()


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    from src.keyboards.main_menu import MainMenuKeyboard
    await callback.message.answer(
        "🏠 Menú principal:",
        reply_markup=MainMenuKeyboard.main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "next_exercise")
async def next_exercise_callback(callback: CallbackQuery, state: FSMContext):
    """Siguiente ejercicio para retos"""
    await callback.answer()
    # Reutilizar la función daily_challenge para nuevo reto
    await daily_challenge(callback, state)


@router.callback_query(F.data == "retry_exercise")
async def retry_exercise_callback(callback: CallbackQuery, state: FSMContext):
    """Reintentar el mismo reto"""
    await callback.answer()
    user_data = await state.get_data()

    if "current_challenge" in user_data:
        # Reiniciar intentos
        await state.update_data({"challenge_attempts": 0})

        challenge_data = user_data["current_challenge"]
        message_text = f"🔄 Reintentando reto...\n\n{challenge_data['pregunta']}\n\n"

        for idx, opcion in enumerate(challenge_data['opciones']):
            message_text += f"{idx + 1}. {opcion}\n"

        await callback.message.answer(message_text, parse_mode="Markdown")