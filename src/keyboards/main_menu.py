from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 Ejercicio")
    builder.button(text="🏆 Reto Diario")
    builder.button(text="📊 Progreso")
    builder.button(text="🎖️ Mis Logros")
    builder.button(text="⚙️ Cambiar Nivel")
    builder.button(text="📚 Curiosidad")
    builder.button(text="👥 Invitar Amigos")
    builder.button(text="💎 Premium")
    builder.button(text="💬 Enviar Opinión")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


class MainMenuKeyboard:
    @staticmethod
    async def build() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.button(text="📝 Ejercicio")
        builder.button(text="🏆 Reto Diario")
        builder.button(text="📊 Progreso")
        builder.button(text="🎖️ Mis Logros")
        builder.button(text="⚙️ Cambiar Nivel")
        builder.button(text="📚 Curiosidad")
        builder.button(text="👥 Invitar Amigos")
        builder.button(text="💎 Premium")
        builder.button(text="💬 Enviar Opinión")
        builder.adjust(2, 2, 2, 2, 1)
        return builder.as_markup(resize_keyboard=True)
