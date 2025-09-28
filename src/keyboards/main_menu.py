# keyboards/main_menu.py - VERSIÓN SIMPLIFICADA Y EFECTIVA
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    """Teclado principal completo y funcional"""
    builder = ReplyKeyboardBuilder()

    buttons = [
        "📝 Ejercicio", "🏆 Reto Diario", "📊 Progreso", "🎖️ Mis Logros",
        "⚙️ Cambiar Nivel", "📚 Curiosidad", "👥 Invitar Amigos",
        "💎 Premium", "💬 Enviar Opinión"
    ]

    # Agregar botones
    for button in buttons:
        builder.add(KeyboardButton(text=button))

    # Disposición: 2 columnas para los primeros 8 botones, 1 columna para el último
    builder.adjust(2, 2, 2, 2, 1)

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False
    )


# Mantener la clase por compatibilidad si es necesaria
class MainMenuKeyboard:
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        return main_menu()

