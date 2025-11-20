# handlers/reto.py - VERSIÓN CORREGIDA
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.keyboards.main_menu import MainMenuKeyboard  # ✅ CORREGIDO
from src.keyboards.inline import challenge_result_keyboard
import json
import logging

router = Router(name="reto")
logger = logging.getLogger(__name__)


def get_superior_level(current_level: str) -> str:
    """Devuelve el nivel superior al actual"""
    levels = ["principiante", "intermedio", "avanzado"]
    try:
        current_index = levels.index(current_level.lower())
        superior_index = min(current_index + 1, len(levels) - 1)
        return levels[superior_index]
    except ValueError:
        return "intermedio"


@router.message(Command("reto"))
@router.callback_query(F.data == "daily_challenge")
async def daily_challenge(message: Message | CallbackQuery, state: FSMContext):
    try:
        # Limpiar estado anterior
        await state.clear()

        if isinstance(message, CallbackQuery):
            await message.answer()  # Confirmar el callback
            message = message.message
            if message.reply_markup:
                await message.edit_reply_markup(reply_markup=None)

        user_id = message.from_user.id

        # Importar aquí para evitar circular import
        from src.services.user_service import UserService
        from src.services.exercise_service import ExerciseService

        # Obtener nivel del usuario y calcular nivel superior para el reto
        user_level = UserService.get_user_level(user_id)
        logger.info(f"Usuario {user_id} - Nivel: {user_level}")

        challenge_level = get_superior_level(user_level)
        logger.info(f"Reto - Nivel objetivo: {challenge_level}")

        # Obtener ejercicio del nivel superior
        exercise = ExerciseService.get_random_exercise(user_id, challenge_level)
        logger.info(f"Ejercicio encontrado: {exercise is not None}")

        if not exercise:
            # Si no hay ejercicios del nivel superior, usar el nivel actual
            exercise = ExerciseService.get_random_exercise(user_id, user_level)
            if not exercise:
                await message.answer(
                    "🎉 ¡Has completado todos los ejercicios disponibles!",
                    reply_markup=MainMenuKeyboard.main_menu()
                )
                return
            else:
                challenge_level = user_level
                logger.info(f"Usando nivel actual: {challenge_level}")

        # Convertir a dict si es un objeto
        if hasattr(exercise, 'to_dict'):
            exercise_data = exercise.to_dict()
        else:
            exercise_data = dict(exercise) if hasattr(exercise, '__dict__') else exercise

        # Convertir opciones si es string JSON
        if isinstance(exercise_data.get('opciones'), str):
            try:
                exercise_data['opciones'] = json.loads(exercise_data['opciones'])
            except json.JSONDecodeError:
                exercise_data['opciones'] = [exercise_data['opciones']]

        # Validar opciones
        options = exercise_data.get('opciones', [])
        if not options or len(options) < 2:
            logger.warning(f"Ejercicio {exercise_data.get('id')} tiene opciones inválidas")
            options = ["Opción A", "Opción B", "Opción C", "Opción D"]
            exercise_data['opciones'] = options

        # Validar índice de respuesta correcta
        correct_index = exercise_data.get("respuesta_correcta", 0)
        if not isinstance(correct_index, int) or correct_index < 0 or correct_index >= len(options):
            correct_index = 0
            logger.warning(f"Índice de respuesta correcta inválido, usando 0")
            exercise_data['respuesta_correcta'] = correct_index

        # Formatear mensaje del reto
        message_text = (
            f"🏆 *Reto Diario - Nivel {challenge_level.upper()}*\n\n"
            f"📚 Categoría: {exercise_data.get('categoria', 'General')}\n\n"
            f"❓ {exercise_data.get('pregunta', '')}\n\n"
        )

        for idx, opcion in enumerate(options):
            message_text += f"   {idx + 1}. {opcion}\n"

        message_text += f"\n💡 *Responde con el número de la opción correcta*"

        # Guardar en estado
        await state.update_data({
            "current_exercise": exercise_data,
            "attempts": 0,
            "exercise_id": exercise_data["id"],
            "exercise_nivel": exercise_data["nivel"],
            "exercise_categoria": exercise_data["categoria"],
            "answer_options": options,
            "state": "waiting_answer",
            "is_challenge": True,
            "challenge_level": challenge_level
        })

        # Importar y usar el teclado de respuestas de exercises.py
        from src.handlers.exercises import create_answer_keyboard
        answer_kb = create_answer_keyboard(options)

        await message.answer(message_text, parse_mode="Markdown", reply_markup=answer_kb)

    except Exception as e:
        logger.error(f"Error completo en daily_challenge: {e}", exc_info=True)
        await message.answer(
            "❌ Ocurrió un error al cargar el reto diario.",
            reply_markup=MainMenuKeyboard.main_menu()
        )


# Handler para el callback "new_challenge"
@router.callback_query(F.data == "new_challenge")
async def new_challenge_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await daily_challenge(callback, state)


# Handler para el callback "challenge_main_menu"
@router.callback_query(F.data == "challenge_main_menu")
async def challenge_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        await state.clear()

        # ✅ CORREGIDO: Usar MainMenuKeyboard directamente
        await callback.message.answer(
            "🏠 Volviendo al menú principal...",
            reply_markup=MainMenuKeyboard.main_menu()
        )

    except Exception as e:
        logger.error(f"Error en challenge_main_menu_callback: {e}")
        await callback.message.answer(
            "❌ Error al volver al menú principal.",
            reply_markup=MainMenuKeyboard.main_menu()
        )