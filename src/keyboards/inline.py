from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def exercise_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado inline específico para ejercicios.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Siguiente", callback_data="next_exercise")
    builder.button(text="📊 Progreso", callback_data="show_progress")
    builder.button(text="🔄 Reintentar", callback_data="retry_exercise")
    builder.adjust(1)
    return builder.as_markup()


def retry_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Intentar de nuevo", callback_data="retry_exercise")
    builder.button(text="📝 Nuevo ejercicio", callback_data="next_exercise")
    builder.button(text="🏠 Menú Principal", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def result_keyboard(is_correct: bool) -> InlineKeyboardMarkup:
    """
    Teclado inline después de responder un ejercicio.
    """
    builder = InlineKeyboardBuilder()
    if is_correct:
        builder.button(text="✅ Continuar", callback_data="next_exercise")
    else:
        builder.button(text="🔄 Reintentar", callback_data="retry_exercise")

    builder.button(text="📊 Ver explicación", callback_data="show_explanation")
    builder.button(text="🏠 Menú principal", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para el menú principal"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Ejercicio Diario", callback_data="daily_exercise")
    builder.button(text="🏆 Reto Diario", callback_data="daily_challenge")
    builder.button(text="📊 Mis Estadísticas", callback_data="my_stats")
    builder.button(text="🔍 Curiosidades", callback_data="curiosities")
    builder.button(text="⚙️ Configuración", callback_data="settings")
    builder.button(text="👥 Invitar Amigos", callback_data="invite_friends")
    builder.adjust(2)  # Dos botones por fila
    return builder.as_markup()


def answer_keyboard(options: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for idx, option in enumerate(options):
        builder.button(text=option, callback_data=f"answer_{idx}")
    builder.adjust(1)
    return builder.as_markup()


def confirmation_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para confirmaciones"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Sí", callback_data="confirm_yes")
    builder.button(text="❌ No", callback_data="confirm_no")
    builder.adjust(2)
    return builder.as_markup()


def stats_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para estadísticas"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📈 Progreso General", callback_data="stats_general")
    builder.button(text="🏆 Logros", callback_data="stats_achievements")
    builder.button(text="📅 Historial", callback_data="stats_history")
    builder.button(text="🏠 Menú Principal", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()