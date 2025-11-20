# handlers/exercises.py - VERSIÓN COMPLETA CON RETOS DIARIOS INTEGRADOS
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
from src.keyboards.inline import result_keyboard, challenge_result_keyboard, retry_keyboard

logger = logging.getLogger(__name__)
router = Router(name="exercises")

MAX_ATTEMPTS = 3
VALID_LEVELS = ["principiante", "intermedio", "avanzado"]


class ExerciseStates:
    WAITING_ANSWER = "waiting_answer"


def escape_markdown_v2(text: str) -> str:
    """
    Escapa caracteres especiales para MarkdownV2 de Telegram.
    Caracteres que deben escaparse: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    if not text:
        return ""

    # Caracteres que deben escaparse con \
    escape_chars = r'([_*\[\]()~`>#+\-=|{}.!])'
    escaped_text = re.sub(escape_chars, r'\\\1', text)

    return escaped_text


def create_answer_keyboard(options: list) -> ReplyKeyboardMarkup:
    """Crea un teclado con las opciones de respuesta"""
    builder = ReplyKeyboardBuilder()

    for option in options:
        # Escapar el texto del botón para evitar problemas
        clean_option = escape_markdown_v2(option)
        builder.add(KeyboardButton(text=clean_option))

    builder.adjust(2)
    builder.row(KeyboardButton(text="❌ Cancelar ejercicio"))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def get_superior_level(current_level: str) -> str:
    """Devuelve el nivel superior al actual"""
    levels = ["principiante", "intermedio", "avanzado"]
    try:
        current_index = levels.index(current_level.lower())
        superior_index = min(current_index + 1, len(levels) - 1)
        return levels[superior_index]
    except ValueError:
        return "intermedio"


async def get_appropriate_exercise(user_id: int, user_level: str) -> tuple:
    """Obtiene un ejercicio apropiado excluyendo los completados"""
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
    """Parsea las opciones del ejercicio"""
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
        message_type: str = None,
        is_challenge: bool = False,
        challenge_level: str = None
) -> None:
    """Envía el mensaje del ejercicio con formato seguro"""
    options = parse_exercise_options(exercise_data)

    # Escapar todos los textos para MarkdownV2
    categoria = escape_markdown_v2(exercise_data.get('categoria', 'General'))
    pregunta = escape_markdown_v2(exercise_data.get('pregunta', ''))
    nivel_used_escaped = escape_markdown_v2(level_used)
    user_level_escaped = escape_markdown_v2(user_level)

    # Determinar el mensaje según sea ejercicio normal o reto
    if is_challenge:
        challenge_level_escaped = escape_markdown_v2(challenge_level)
        message_text = (
            f"🏆 *Reto Diario \\- Nivel {challenge_level_escaped.upper()}*\n\n"
            f"📚 Categoría\\: {categoria}\n\n"
            f"{pregunta}\n\n"
            "💡 *Selecciona tu respuesta\\:*"
        )
    else:
        message_text = (
            f"📚 *Ejercicio de {categoria} \\({nivel_used_escaped}\\)*\n\n"
            f"{pregunta}\n\n"
            "💡 *Selecciona tu respuesta\\:*"
        )

    # Mensajes informativos para ejercicios normales
    if not is_challenge:
        if message_type == "alternative_level":
            message_text = (
                    f"🎯 *¡Has completado todos los ejercicios de tu nivel \\({user_level_escaped}\\)\\!*\n"
                    f"*Te mostramos un ejercicio del nivel {nivel_used_escaped}\\:*\n\n" + message_text
            )
        elif level_used != user_level:
            message_text = (
                    f"🎯 *Ejercicio del nivel {nivel_used_escaped} "
                    f"\\(tu nivel actual es {user_level_escaped}\\)*\n\n" + message_text
            )

    answer_kb = create_answer_keyboard(options)

    await message.answer(message_text, parse_mode="MarkdownV2", reply_markup=answer_kb)


async def handle_correct_answer(
        message: Message,
        exercise_data: Dict,
        user_data: Dict,
        attempts: int
) -> None:
    """Maneja una respuesta correcta"""
    user_id = message.from_user.id

    success = ExerciseService.mark_exercise_completed(
        user_id=user_id,
        exercise_id=user_data["exercise_id"],
        nivel=user_data["exercise_nivel"],
        categoria=user_data["exercise_categoria"],
        is_correct=True,
        attempts=attempts
    )

    if not success:
        logger.warning(f"No se pudo marcar el ejercicio {user_data['exercise_id']} como completado")

    explanation = escape_markdown_v2(
        exercise_data.get('explicacion', '¡Excelente trabajo! Has acertado la respuesta.')
    )

    # Determinar si es reto o ejercicio normal
    is_challenge = user_data.get("is_challenge", False)

    if is_challenge:
        challenge_level = user_data.get("challenge_level", "desconocido").upper()
        await message.answer(
            f"✅ *¡Correcto\\!* \\+1 punto\n\n"
            f"💡 *Explicación\\:* {explanation}\n\n"
            f"🏅 ¡Has superado un reto de nivel {escape_markdown_v2(challenge_level)}\\!",
            reply_markup=challenge_result_keyboard(),
            parse_mode="MarkdownV2"
        )
    else:
        await message.answer(
            f"✅ *¡Correcto\\!* \\+1 punto\n\n"
            f"💡 *Explicación\\:* {explanation}",
            reply_markup=result_keyboard(is_correct=True),
            parse_mode="MarkdownV2"
        )


async def handle_incorrect_answer(
        message: Message,
        exercise_data: Dict,
        user_data: Dict,
        attempts: int,
        answer_options: list,
        state: FSMContext
) -> None:
    """Maneja una respuesta incorrecta"""
    if attempts >= MAX_ATTEMPTS:
        # Agotó los intentos
        correct_answer = escape_markdown_v2(answer_options[exercise_data["respuesta_correcta"]])
        explanation = escape_markdown_v2(
            exercise_data.get('explicacion', 'Sigue practicando para mejorar.')
        )

        # Marcar como completado
        ExerciseService.mark_exercise_completed(
            user_id=message.from_user.id,
            exercise_id=user_data["exercise_id"],
            nivel=user_data["exercise_nivel"],
            categoria=user_data["exercise_categoria"],
            is_correct=False,
            attempts=attempts
        )

        # Determinar si es reto o ejercicio normal
        is_challenge = user_data.get("is_challenge", False)

        if is_challenge:
            await message.answer(
                f"❌ *La respuesta correcta era\\:* {correct_answer}\n\n"
                f"💡 *Explicación\\:* {explanation}",
                reply_markup=challenge_result_keyboard(),
                parse_mode="MarkdownV2"
            )
        else:
            await message.answer(
                f"❌ *La respuesta correcta era\\:* {correct_answer}\n\n"
                f"💡 *Explicación\\:* {explanation}",
                reply_markup=result_keyboard(is_correct=False),
                parse_mode="MarkdownV2"
            )
        await state.clear()
    else:
        # Intentar nuevamente
        await state.update_data({"attempts": attempts})
        await message.answer(
            f"❌ Incorrecto\\. Intenta nuevamente \\(intento {attempts}/{MAX_ATTEMPTS}\\)\\:",
            reply_markup=create_answer_keyboard(answer_options),
            parse_mode="MarkdownV2"
        )


async def setup_exercise_state(
        state: FSMContext,
        exercise_data: Dict,
        is_challenge: bool = False,
        challenge_level: str = None
) -> None:
    """Configura el estado para un ejercicio (normal o reto)"""
    options = parse_exercise_options(exercise_data)

    # Validar índice de respuesta correcta
    correct_index = exercise_data.get("respuesta_correcta", 0)
    if not isinstance(correct_index, int) or correct_index < 0 or correct_index >= len(options):
        correct_index = 0
        logger.warning(f"Índice de respuesta correcta inválido")

    exercise_data['respuesta_correcta'] = correct_index

    # Configurar estado base
    state_data = {
        "current_exercise": exercise_data,
        "attempts": 0,
        "exercise_id": exercise_data["id"],
        "exercise_nivel": exercise_data["nivel"],
        "exercise_categoria": exercise_data["categoria"],
        "answer_options": options,
        "state": ExerciseStates.WAITING_ANSWER
    }

    # Agregar datos específicos de reto si es necesario
    if is_challenge:
        state_data["is_challenge"] = True
        state_data["challenge_level"] = challenge_level

    await state.update_data(state_data)


@router.message(Command("ejercicio"))
@router.message(F.text == "📝 Ejercicio")
async def cmd_exercise(message: Message, state: FSMContext):
    """Maneja el comando para empezar un nuevo ejercicio"""
    try:
        await state.clear()
        user_id = message.from_user.id
        user_level = UserService.get_user_level(user_id)

        exercise, level_used, message_type = await get_appropriate_exercise(user_id, user_level)

        if not exercise:
            if message_type == "no_exercises":
                await message.answer(
                    "🎉 ¡Felicidades\\! Has completado todos los ejercicios disponibles\\.\n\n"
                    "Pronto añadiremos más contenido\\. ¡Mantente atento\\!",
                    reply_markup=MainMenuKeyboard.main_menu(),
                    parse_mode="MarkdownV2"
                )
            return

        # Convertir a dict si es un objeto
        if hasattr(exercise, 'to_dict'):
            exercise_data = exercise.to_dict()
        else:
            exercise_data = dict(exercise) if hasattr(exercise, '__dict__') else exercise

        # Configurar estado para ejercicio normal
        await setup_exercise_state(state, exercise_data)

        await send_exercise_message(
            message,
            exercise_data,
            level_used,
            user_level,
            message_type,
            is_challenge=False
        )

    except Exception as e:
        logger.error(f"Error en cmd_exercise para usuario {message.from_user.id}: {e}", exc_info=True)
        await message.answer(
            "❌ Error al cargar el ejercicio. Intenta nuevamente.",
            reply_markup=MainMenuKeyboard.main_menu(),
            parse_mode=None
        )


# handlers/exercises.py - AGREGAR DESPUÉS DEL HANDLER DE EJERCICIO

@router.message(F.text == "🏆 Reto Diario")
async def handle_reto_diario_button(message: Message, state: FSMContext):
    """Maneja el botón '🏆 Reto Diario' del menú principal"""
    try:
        logger.info(f"🎯 Botón 'Reto Diario' presionado por usuario {message.from_user.id}")

        # Usar la misma función que usa el comando /reto
        await cmd_challenge(message, state)

    except Exception as e:
        logger.error(f"❌ Error en handle_reto_diario_button: {e}", exc_info=True)
        await message.answer(
            "❌ Error al cargar el reto diario.",
            reply_markup=MainMenuKeyboard.main_menu()
        )

@router.message(Command("reto"))
@router.callback_query(F.data == "daily_challenge")
async def cmd_challenge(message: Message | CallbackQuery, state: FSMContext):
    """Maneja el comando para empezar un reto diario"""
    try:
        await state.clear()

        if isinstance(message, CallbackQuery):
            await message.answer()
            message = message.message
            if message.reply_markup:
                await message.edit_reply_markup(reply_markup=None)

        user_id = message.from_user.id
        user_level = UserService.get_user_level(user_id)

        # Obtener nivel superior para el reto
        challenge_level = get_superior_level(user_level)

        # Obtener ejercicio del nivel superior
        exercise = ExerciseService.get_random_exercise(user_id, challenge_level)

        if not exercise:
            # Si no hay ejercicios del nivel superior, usar el nivel actual
            exercise = ExerciseService.get_random_exercise(user_id, user_level)
            if not exercise:
                await message.answer(
                    "🎉 ¡Has completado todos los ejercicios disponibles!",
                    reply_markup=MainMenuKeyboard.main_menu(),
                    parse_mode=None
                )
                return
            else:
                challenge_level = user_level

        # Convertir a dict si es un objeto
        if hasattr(exercise, 'to_dict'):
            exercise_data = exercise.to_dict()
        else:
            exercise_data = dict(exercise) if hasattr(exercise, '__dict__') else exercise

        # Configurar estado para reto
        await setup_exercise_state(
            state,
            exercise_data,
            is_challenge=True,
            challenge_level=challenge_level
        )

        await send_exercise_message(
            message,
            exercise_data,
            challenge_level,
            user_level,
            is_challenge=True,
            challenge_level=challenge_level
        )

    except Exception as e:
        logger.error(f"Error en cmd_challenge para usuario {message.from_user.id}: {e}", exc_info=True)
        await message.answer(
            "❌ Error al cargar el reto diario. Intenta nuevamente.",
            reply_markup=MainMenuKeyboard.main_menu(),
            parse_mode=None
        )


@router.message(F.text == "❌ Cancelar ejercicio")
async def cancel_exercise(message: Message, state: FSMContext):
    """Cancelar el ejercicio actual"""
    await state.clear()
    await message.answer(
        "❌ Ejercicio cancelado. Volviendo al menú principal...",
        reply_markup=MainMenuKeyboard.main_menu(),
        parse_mode=None
    )


@router.message(F.text)
async def handle_exercise_answer(message: Message, state: FSMContext):
    """Maneja las respuestas a los ejercicios (normales y retos)"""
    try:
        user_data = await state.get_data()
        # Validar que el ejercicio en espera no captura otros mensajes
        if user_data.get("state") != ExerciseStates.WAITING_ANSWER:
            return

        answer_options = user_data.get("answer_options", [])
        selected_text = message.text

        # Manejar cancelación
        if selected_text == "❌ Cancelar ejercicio":
            await cancel_exercise(message, state)
            return

        # Validar opción seleccionada
        if selected_text not in answer_options:
            options_text = "\n".join([f"• {opt}" for opt in answer_options])
            await message.answer(
                f"❌ Opción no válida. Selecciona una de:\n\n{options_text}",
                parse_mode=None
            )
            return

        user_id = message.from_user.id
        exercise_data = user_data["current_exercise"]
        selected_option = answer_options.index(selected_text)
        attempts = user_data.get("attempts", 0) + 1

        is_correct = selected_option == exercise_data["respuesta_correcta"]

        if is_correct:
            await handle_correct_answer(message, exercise_data, user_data, attempts)
            await state.clear()
        else:
            await handle_incorrect_answer(
                message, exercise_data, user_data, attempts, answer_options, state
            )

    except Exception as e:
        logger.error(f"Error en handle_exercise_answer para usuario {message.from_user.id}: {e}", exc_info=True)
        await message.answer(
            "❌ Error al procesar tu respuesta. Intenta nuevamente.",
            reply_markup=MainMenuKeyboard.main_menu(),
            parse_mode=None
        )
        await state.clear()


@router.callback_query(F.data == "next_exercise")
async def next_exercise(callback: CallbackQuery, state: FSMContext):
    """Maneja el callback para siguiente ejercicio"""
    try:
        await callback.answer()

        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"No se pudo eliminar el mensaje: {e}")
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except:
                pass

        await state.clear()
        await cmd_exercise(callback.message, state)

    except Exception as e:
        logger.error(f"Error en next_exercise: {e}", exc_info=True)
        await callback.message.answer(
            "❌ Error al cargar el siguiente ejercicio.",
            reply_markup=MainMenuKeyboard.main_menu(),
            parse_mode=None
        )


@router.callback_query(F.data == "new_challenge")
async def new_challenge_callback(callback: CallbackQuery, state: FSMContext):
    """Maneja el callback para nuevo reto"""
    try:
        await callback.answer()

        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"No se pudo eliminar el mensaje: {e}")
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except:
                pass

        await state.clear()
        await cmd_challenge(callback.message, state)

    except Exception as e:
        logger.error(f"Error en new_challenge_callback: {e}", exc_info=True)
        await callback.message.answer(
            "❌ Error al cargar el nuevo reto.",
            reply_markup=MainMenuKeyboard.main_menu(),
            parse_mode=None
        )


@router.callback_query(F.data == "challenge_main_menu")
async def challenge_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Maneja el callback para menú principal desde reto"""
    try:
        await callback.answer()
        await state.clear()

        await callback.message.answer(
            "🏠 Volviendo al menú principal...",
            reply_markup=MainMenuKeyboard.main_menu(),
            parse_mode=None
        )

    except Exception as e:
        logger.error(f"Error en challenge_main_menu_callback: {e}", exc_info=True)
        await callback.message.answer(
            "❌ Error al volver al menú principal.",
            reply_markup=MainMenuKeyboard.main_menu(),
            parse_mode=None
        )


@router.callback_query(F.data == "retry_exercise")
async def retry_exercise(callback: CallbackQuery, state: FSMContext):
    """Maneja el callback para reintentar ejercicio"""
    try:
        await callback.answer()

        try:
            await callback.message.delete()
        except:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except:
                pass

        await cmd_exercise(callback.message, state)

    except Exception as e:
        logger.error(f"Error en retry_exercise: {e}", exc_info=True)
        await callback.message.answer(
            "❌ Error al reintentar el ejercicio.",
            reply_markup=MainMenuKeyboard.main_menu(),
            parse_mode=None
        )


@router.callback_query(F.data == "show_progress")
async def show_progress_callback(callback: CallbackQuery):
    """Maneja el callback para mostrar progreso"""
    try:
        await callback.answer()
        user_id = callback.from_user.id

        stats = ExerciseService.get_user_stats(user_id)

        if not stats:
            await callback.message.answer(
                "📊 Aún no tienes estadísticas. ¡Completa algunos ejercicios!",
                parse_mode=None
            )
            return

        progress_text = (
            f"📊 **Tu Progreso**\n\n"
            f"🏅 Nivel: {escape_markdown_v2(stats.get('level', 'No establecido'))}\n"
            f"✅ Ejercicios completados: {stats.get('total_exercises', 0)}\n"
            f"🎯 Respuestas correctas: {stats.get('correct_exercises', 0)}\n"
            f"📚 Categorías diferentes: {stats.get('categories_count', 0)}\n"
            f"🌟 Niveles practicados: {stats.get('levels_count', 0)}"
        )

        if stats.get('exercises_by_level'):
            progress_text += "\n\n📈 **Por nivel:**"
            for nivel, count in stats['exercises_by_level'].items():
                progress_text += f"\n• {escape_markdown_v2(nivel)}: {count}"

        if stats.get('exercises_by_category'):
            progress_text += "\n\n📚 **Por categoría:**"
            for categoria, count in stats['exercises_by_category'].items():
                progress_text += f"\n• {escape_markdown_v2(categoria)}: {count}"

        await callback.message.answer(progress_text, parse_mode="MarkdownV2")

    except Exception as e:
        logger.error(f"Error en show_progress_callback: {e}", exc_info=True)
        await callback.message.answer(
            "❌ Error al cargar el progreso.",
            parse_mode=None
        )