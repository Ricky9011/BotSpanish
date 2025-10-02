# handlers/curiosities.py - VERSIÓN CORREGIDA
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from src.services.curiosity_service import CuriosityService
from src.keyboards.main_menu import MainMenuKeyboard
from src.keyboards.inline import curiosity_keyboard

logger = logging.getLogger(__name__)
router = Router(name="curiosities")

# ✅ SOLO UN HANDLER para mensajes
@router.message(Command("curiosidad", "curiosidades"))
@router.message(F.text == "📚 Curiosidad")  # ✅ TEXTO CORREGIDO
async def handle_curiosidad_message(message: Message, state: FSMContext):
    """Maneja el comando /curiosidad y el botón del teclado principal"""
    try:
        logger.info(f"📚 Curiosidad solicitada via mensaje por {message.from_user.id}")
        await state.clear()

        curiosity = CuriosityService.get_random_curiosity()
        if curiosity:
            categoria = getattr(curiosity, 'categoria', 'General')
            texto_curiosidad = getattr(curiosity, 'texto', 'Texto no disponible')

            await message.answer(
                f"🧠 Curiosidad del español - {categoria}\n\n{texto_curiosidad}",
                reply_markup=curiosity_keyboard()
            )
        else:
            await message.answer(
                "📚 No hay curiosidades disponibles en este momento.",
                reply_markup=MainMenuKeyboard.main_menu()
            )

    except Exception as e:
        logger.error(f"Error en handle_curiosidad_message: {e}")
        await message.answer(
            "❌ Error al cargar la curiosidad. Intenta nuevamente.",
            reply_markup=MainMenuKeyboard.main_menu()
        )

# ✅ SOLO UN HANDLER para callbacks
@router.callback_query(F.data == "show_curiosity")
async def show_curiosity_callback(callback: CallbackQuery, state: FSMContext):
    """Handler único para callbacks de curiosidad"""
    try:
        logger.info(f"🔍 Callback show_curiosity recibido de {callback.from_user.id}")
        await callback.answer()
        await state.clear()

        curiosity = CuriosityService.get_random_curiosity()
        if curiosity:
            categoria = getattr(curiosity, 'categoria', 'General')
            texto_curiosidad = getattr(curiosity, 'texto', 'Texto no disponible')

            await callback.message.answer(
                f"🧠 Curiosidad del español - {categoria}\n\n{texto_curiosidad}",
                reply_markup=curiosity_keyboard()
            )
        else:
            await callback.message.answer(
                "📚 No hay curiosidades disponibles",
                reply_markup=MainMenuKeyboard.main_menu()
            )
    except Exception as e:
        logger.error(f"Error en show_curiosity callback: {e}")
        await callback.answer("❌ Error al cargar curiosidad", show_alert=True)

