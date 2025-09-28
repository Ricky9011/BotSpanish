# handlers/curiosities.py - VERSIÓN COMPLETAMENTE CORREGIDA
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from src.services.curiosity_service import CuriosityService
from src.keyboards.main_menu import MainMenuKeyboard
from src.keyboards.inline import curiosity_keyboard
from src.utils import sanitize_text

logger = logging.getLogger(__name__)
router = Router(name="curiosities")


@router.message(Command("curiosidad"))
@router.message(F.text == "📚 Curiosidad")
async def cmd_curiosidad(message: Message, state: FSMContext):
    """Maneja el comando de curiosidades - VERSIÓN CORREGIDA"""
    try:
        logger.info(f"Comando curiosidad recibido de usuario {message.from_user.id}")
        await state.clear()

        # ✅ Verificar disponibilidad primero
        curiosity_count = CuriosityService.get_curiosity_count()
        logger.info(f"Curiosidades disponibles: {curiosity_count}")

        if curiosity_count == 0:
            await message.answer(
                "📚 No hay curiosidades disponibles en este momento.\n\n"
                "Por favor, contacta al administrador para añadir más contenido.",
                reply_markup=MainMenuKeyboard.main_menu(),
                parse_mode=None
            )
            return

        # ✅ Obtener curiosidad aleatoria
        curiosity = CuriosityService.get_random_curiosity()

        if not curiosity:
            logger.error("No se pudo obtener ninguna curiosidad a pesar de que hay disponibles")
            await message.answer(
                "❌ Error temporal al cargar la curiosidad. Intenta nuevamente.",
                reply_markup=MainMenuKeyboard.main_menu(),
                parse_mode=None
            )
            return

        # ✅ Extraer datos de forma segura
        categoria = getattr(curiosity, 'categoria', 'General')
        texto_curiosidad = getattr(curiosity, 'texto', 'Texto no disponible')

        logger.info(f"Curiosidad obtenida - Categoría: {categoria}, Texto: {texto_curiosidad[:50]}...")

        # ✅ Formatear mensaje correctamente (sin Markdown para evitar errores)
        message_text = (
            f"🧠 Curiosidad del español - {categoria}\n\n"
            f"{texto_curiosidad}"
        )

        await message.answer(
            message_text,
            parse_mode=None,  # ✅ Sin formato para evitar errores
            reply_markup=curiosity_keyboard()
        )
        logger.info("Curiosidad enviada exitosamente")

    except Exception as e:
        logger.error(f"Error en cmd_curiosidad: {e}", exc_info=True)
        await message.answer(
            "❌ Error al cargar la curiosidad. Intenta más tarde.",
            reply_markup=MainMenuKeyboard.main_menu(),
            parse_mode=None
        )


@router.callback_query(F.data == "show_curiosity")
async def show_curiosity_callback(callback: CallbackQuery, state: FSMContext):
    """Muestra una curiosidad aleatoria - VERSIÓN CORREGIDA"""
    try:
        logger.info(f"Callback show_curiosity recibido de usuario {callback.from_user.id}")
        await callback.answer()

        # ✅ Verificar disponibilidad
        curiosity_count = CuriosityService.get_curiosity_count()
        if curiosity_count == 0:
            await callback.message.answer(
                "📚 No hay curiosidades disponibles en este momento.",
                reply_markup=MainMenuKeyboard.main_menu(),
                parse_mode=None
            )
            return

        # ✅ Obtener curiosidad
        curiosity = CuriosityService.get_random_curiosity()

        if not curiosity:
            await callback.message.answer(
                "❌ Error al cargar la curiosidad. Intenta nuevamente.",
                parse_mode=None
            )
            return

        categoria = getattr(curiosity, 'categoria', 'General')
        texto_curiosidad = getattr(curiosity, 'texto', 'Texto no disponible')

        message_text = (
            f"🧠 Curiosidad del español - {categoria}\n\n"
            f"{texto_curiosidad}"
        )

        await callback.message.answer(
            message_text,
            parse_mode=None,  # ✅ Sin formato para evitar errores
            reply_markup=curiosity_keyboard()
        )
        logger.info("Curiosidad desde callback enviada exitosamente")

    except Exception as e:
        logger.error(f"Error en show_curiosity_callback: {e}", exc_info=True)
        await callback.message.answer(
            "❌ Error al cargar la curiosidad.",
            parse_mode=None
        )


@router.callback_query(F.data == "curiosities")
async def curiosities_callback(callback: CallbackQuery, state: FSMContext):
    """Callback alternativo para curiosidades"""
    await show_curiosity_callback(callback, state)


# ✅ Asegurar que el router se exporta correctamente
__all__ = ['router']