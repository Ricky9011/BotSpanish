# keyboards/inline.py - VERSIÓN CORREGIDA
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def exercise_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado inline específico para ejercicios - CORREGIDO
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Siguiente ejercicio", callback_data="next_exercise")
    builder.button(text="📚 Curiosidad",
                   callback_data="show_curiosity")  # 🔥 CAMBIO: Ver curiosidad en lugar de progreso
    builder.button(text="🔄 Reintentar", callback_data="retry_exercise")
    builder.adjust(1)
    return builder.as_markup()


def retry_keyboard() -> InlineKeyboardMarkup:
    """Teclado para reintentar - CORREGIDO"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Intentar de nuevo", callback_data="retry_exercise")
    builder.button(text="📝 Nuevo ejercicio", callback_data="next_exercise")
    builder.button(text="📚 Curiosidad", callback_data="show_curiosity")  # 🔥 CAMBIO: Añadir curiosidad
    builder.button(text="🏠 menú principal", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def result_keyboard(is_correct: bool) -> InlineKeyboardMarkup:
    """
    Teclado inline después de responder un ejercicio - CORREGIDO
    """
    builder = InlineKeyboardBuilder()

    if is_correct:
        builder.button(text="➡️ Siguiente ejercicio", callback_data="next_exercise")
        builder.button(text="📚 Curiosidad",
                       callback_data="show_curiosity")  # 🔥 CAMBIO: Ver curiosidad en lugar de explicación
    else:
        builder.button(text="🔄 Reintentar ejercicio", callback_data="retry_exercise")
        builder.button(text="💡 Ver explicación",
                       callback_data="show_explanation")  # Mantener explicación para incorrectos

    builder.button(text="📊 Ver progreso", callback_data="show_progress")
    builder.button(text="🏠 menú principal", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para el menú principal"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Ejercicio Diario", callback_data="daily_exercise")
    builder.button(text="🏆 Reto Diario", callback_data="daily_challenge")
    builder.button(text="📊 Mis Estadísticas", callback_data="my_stats")
    builder.button(text="📚 Curiosidad", callback_data="show_curiosity")
    builder.button(text="💬 Enviar Opinión", callback_data="send_feedback")
    builder.button(text="⚙️ Cambiar Nivel", callback_data="change_level")
    builder.button(text="⚙️ Configuración", callback_data="settings")
    builder.button(text="👥 Invitar Amigos", callback_data="invite_friends")
    builder.adjust(2)
    return builder.as_markup()


def curiosity_keyboard() -> InlineKeyboardMarkup:
    """Teclado específico para curiosidades"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Curiosidad", callback_data="show_curiosity")
    builder.button(text="📝 Hacer ejercicio", callback_data="next_exercise")
    builder.button(text="🏠 menú principal", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def answer_keyboard(options: list) -> InlineKeyboardMarkup:
    """Teclado para opciones de respuesta"""
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
    builder.button(text="📚 Curiosidad", callback_data="show_curiosity")  # 🔥 CAMBIO: Añadir curiosidad
    builder.button(text="🏠 menú principal", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
