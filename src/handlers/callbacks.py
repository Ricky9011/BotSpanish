# handlers/callbacks.py - VERSIÓN COMPLETA
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from src.keyboards.main_menu import MainMenuKeyboard

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Handler para volver al menú principal desde cualquier parte"""
    try:
        await state.clear()  # Limpiar cualquier estado activo
        await callback.message.answer(
            "🏠 Menú principal:",
            reply_markup=MainMenuKeyboard.main_menu()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error en main_menu callback: {e}")
        await callback.answer("❌ Error al volver al menú")

@router.callback_query(F.data == "show_curiosity")
async def show_curiosity_callback(callback: CallbackQuery, state: FSMContext):
    """Handler para mostrar curiosidades desde callbacks"""
    try:
        await callback.answer()
        # Importar aquí para evitar circular imports
        from src.handlers.curiosities import cmd_curiosidad
        await state.clear()
        await cmd_curiosidad(callback.message, state)
    except Exception as e:
        logger.error(f"Error en show_curiosity callback: {e}")
        await callback.answer("❌ Error al cargar curiosidad")

@router.callback_query(F.data == "next_exercise")
async def next_exercise_callback(callback: CallbackQuery, state: FSMContext):
    """Handler para siguiente ejercicio"""
    try:
        await callback.answer()
        # Importar aquí para evitar circular imports
        from src.handlers.exercises import cmd_exercise
        await state.clear()
        await cmd_exercise(callback.message, state)
    except Exception as e:
        logger.error(f"Error en next_exercise callback: {e}")
        await callback.answer("❌ Error al cargar ejercicio")

@router.callback_query(F.data == "retry_exercise")
async def retry_exercise_callback(callback: CallbackQuery, state: FSMContext):
    """Handler para reintentar ejercicio"""
    try:
        await callback.answer()
        # Importar aquí para evitar circular imports
        from src.handlers.exercises import cmd_exercise
        await state.clear()
        await cmd_exercise(callback.message, state)
    except Exception as e:
        logger.error(f"Error en retry_exercise callback: {e}")
        await callback.answer("❌ Error al reintentar ejercicio")

@router.callback_query(F.data == "show_progress")
async def show_progress_callback(callback: CallbackQuery):
    """Handler para mostrar progreso"""
    try:
        await callback.answer()
        # Importar aquí para evitar circular imports
        from src.handlers.exercises import show_progress_callback as show_progress
        await show_progress(callback)
    except Exception as e:
        logger.error(f"Error en show_progress callback: {e}")
        await callback.answer("❌ Error al cargar progreso")

@router.callback_query(F.data == "daily_challenge")
async def daily_challenge_callback(callback: CallbackQuery, state: FSMContext):
    """Handler para reto diario"""
    try:
        await callback.answer()
        # Importar aquí para evitar circular imports
        from src.handlers.reto import daily_challenge
        await state.clear()
        await daily_challenge(callback, state)
    except Exception as e:
        logger.error(f"Error en daily_challenge callback: {e}")
        await callback.answer("❌ Error al cargar reto")