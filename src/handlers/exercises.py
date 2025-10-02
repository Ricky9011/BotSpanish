# handlers/exercises.py - VERSIÓN CORREGIDA
import json
import logging
import re
from typing import Dict, Any, Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from src.keyboards.main_menu import MainMenuKeyboard
from src.services.user_service import UserService
from src.services.exercise_service import ExerciseService
from src.keyboards.inline import exercise_keyboard, retry_keyboard, result_keyboard

# Configuración del logger
logger = logging.getLogger(__name__)
router = Router(name="exercises")

# Constantes globales
MAX_ATTEMPTS = 3  # Número máximo de intentos permitidos
VALID_LEVELS = ["principiante", "intermedio", "avanzado"]  # Niveles válidos de ejercicios


class ExerciseStates:
    """Clase para definir los estados de los ejercicios."""
    WAITING_ANSWER = "waiting_answer"  # Estado de espera de respuesta


def escape_markdown_v2(text: str) -> str:
    """
    Escapa caracteres especiales para MarkdownV2 de Telegram.

    :param text: Texto a escapar.
    :return: Texto con los caracteres especiales escapados.
    """
    if not text:
        return ""

    # Caracteres que deben escaparse con \
    escape_chars = r'([_*\[\]()~`>#+\-=|{}.!])'
    escaped_text = re.sub(escape_chars, r'\\\1', text)

    return escaped_text


def create_answer_keyboard(options: list) -> ReplyKeyboardMarkup:
    """
    Crea un teclado con las opciones de respuesta.

    :param options: Lista de opciones para los botones.
    :return: Teclado de respuesta con las opciones proporcionadas.
    """
    builder = ReplyKeyboardBuilder()

    for option in options:
        # Escapar el texto del botón para evitar problemas
        clean_option = escape_markdown_v2(option)
        builder.add(KeyboardButton(text=clean_option))

    builder.adjust(2)  # Ajusta el teclado a 2 columnas
    builder.row(KeyboardButton(text="❌ Cancelar ejercicio"))  # Botón para cancelar

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


async def get_appropriate_exercise(user_id: int, user_level: str) -> tuple:
    """
    Obtiene un ejercicio apropiado excluyendo los ya completados.

    :param user_id: ID del usuario.
    :param user_level: Nivel actual del usuario.
    :return: Tupla con el ejercicio, nivel usado y tipo de mensaje.
    """
    # 1. Intentar con el nivel del usuario
    exercise = ExerciseService.get_random_exercise(user_id, user_level)
    if exercise:
        return exercise, user_level, None

    # 2. Buscar en otros niveles
    other_levels = [lvl for lvl in VALID_LEVELS if lvl != user_level]

    for level in other_levels:
        exercise = ExerciseService.get_random_exercise(user_id, level)
        if exercise:
            return exercise, level, "alternative_level"

    return None, None, "no_exercises"


def parse_exercise_options(exercise_data: Dict) -> list:
    """
    Parsear las opciones del ejercicio.

    :param exercise_data: Diccionario con los datos del ejercicio.
    :return: Lista de opciones procesadas.
    """
    options = exercise_data.get("opciones", [])

    if isinstance(options, str):
        try:
            return json.loads(options)
        except json.JSONDecodeError:
            if ',' in options:
                return [opt.strip() for opt in options.split(',')]
            return [options]

    return options


async def send_exercise_message(
        message: Message,
        exercise_data: Dict,
        level_used: str,
        user_level: str,
        message_type: str = None
) -> None:
    """
    Envía el mensaje del ejercicio con formato seguro.

    :param message: Objeto del mensaje recibido.
    :param exercise_data: Datos del ejercicio.
    :param level_used: Nivel usado para el ejercicio.
    :param user_level: Nivel actual del usuario.
    :param message_type: Tipo de mensaje adicional (opcional).
    """
    options = parse_exercise_options(exercise_data)

    # Escapar todos los textos para MarkdownV2
    categoria = escape_markdown_v2(exercise_data.get('categoria', 'General'))
    pregunta = escape_markdown_v2(exercise_data.get('pregunta', ''))
    nivel_used_escaped = escape_markdown_v2(level_used)
    user_level_escaped = escape_markdown_v2(user_level)

    message_text = (
        f"📚 *Ejercicio de {categoria} \\({nivel_used_escaped}\\)*\n\n"
        f"{pregunta}\n\n"
        "💡 *Selecciona tu respuesta:*"
    )

    # Mensajes informativos
    if message_type == "alternative_level":
        message_text = (
                f"🎯 *¡Has completado todos los ejercicios de tu nivel \\({user_level_escaped}\\)\\!*\n"
                f"*Te mostramos un ejercicio del nivel {nivel_used_escaped}:*\n\n" + message_text
        )
    elif level_used != user_level:
        message_text = (
                f"🎯 *Ejercicio del nivel {nivel_used_escaped} "
                f"\\(tu nivel actual es {user_level_escaped}\\)*\n\n" + message_text
        )

    answer_kb = create_answer_keyboard(options)

    # Enviar el mensaje con el teclado
    await message.answer(message_text, parse_mode="MarkdownV2", reply_markup=answer_kb)


