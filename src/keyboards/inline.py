from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def exercise_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Siguiente Ejercicio", callback_data="next_exercise")
    builder.button(text="📊 Ver Progreso", callback_data="show_progress")
    builder.button(text="🏆 Reto Diario", callback_data="daily_challenge")
    builder.adjust(1)
    return builder.as_markup()


def retry_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Intentar de nuevo", callback_data="retry_exercise")
    builder.button(text="📝 Nuevo ejercicio", callback_data="next_exercise")
    builder.adjust(1)
    return builder.as_markup()
