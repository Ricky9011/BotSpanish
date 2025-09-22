from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def build_main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        "📝 Ejercicio", "🏆 Reto Diario", "📊 Progreso", "🎖️ Mis Logros",
        "⚙️ Cambiar Nivel", "📚 Curiosidad", "👥 Invitar Amigos",
        "💎 Premium", "💬 Enviar Opinión"
    ]
    builder.add(*buttons)
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

class MainMenuKeyboard:
    @staticmethod
    async def build() -> ReplyKeyboardMarkup:
        return build_main_menu_keyboard()

def main_menu() -> ReplyKeyboardMarkup:
    return build_main_menu_keyboard()
