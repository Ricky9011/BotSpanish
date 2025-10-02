# handlers/reto.py - VERSIÓN UNIFICADA
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.services.answer_service import verify_answer_logic
from src.keyboards.inline import result_keyboard, exercise_keyboard
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
        challenge_level = get_superior_level(user_level)

        # Obtener ejercicio del nivel superior
        exercise = ExerciseService.get_random_exercise(user_id, challenge_level)

        if not exercise:
            # Si no hay ejercicios del nivel superior, usar el nivel actual
            exercise = ExerciseService.get_random_exercise(user_id, user_level)
            if not exercise:
                await message.answer("🎉 ¡Has completado todos los ejercicios disponibles!")
                return
            else:
                challenge_level = user_level

        # Convertir opciones si es string JSON
        if isinstance(exercise.opciones, str):
            try:
                exercise.opciones = json.loads(exercise.opciones)
            except json.JSONDecodeError:
                exercise.opciones = [exercise.opciones]

        # Crear diccionario de datos del ejercicio (MISMA ESTRUCTURA que ejercicios normales)
        exercise_data = {
            "id": exercise.id,
            "categoria": exercise.categoria,
            "nivel": exercise.nivel,
            "pregunta": exercise.pregunta,
            "opciones": exercise.opciones,
            "respuesta_correcta": exercise.respuesta_correcta,
            "explicacion": exercise.explicacion
        }

        # Formatear mensaje del reto (MISMO FORMATO que ejercicios normales)
        message_text = (
            f"🏆 *Reto Diario - Nivel {challenge_level.upper()}*\n\n"
            f"📚 Categoría: {exercise.categoria}\n\n"
            f"❓ {exercise.pregunta}\n\n"
        )

        for idx, opcion in enumerate(exercise.opciones):
            message_text += f"   {idx + 1}. {opcion}\n"

        message_text += f"\💡 *Responde con el número de la opción correcta*"

        # Guardar en estado (MISMA ESTRUCTURA que ejercicios normales)
        await state.update_data({
            "current_exercise": exercise_data,  # MISMO NOMBRE que en ejercicios
            "attempts": 0,  # MISMO NOMBRE que en ejercicios
            "exercise_id": exercise.id,
            "exercise_nivel": exercise.nivel,
            "exercise_categoria": exercise.categoria,
            "is_challenge": True,  # Bandera para identificar que es un reto
            "challenge_level": challenge_level
        })

        await message.answer(message_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error en daily_challenge: {e}")
        await message.answer("❌ Ocurrió un error al cargar el reto diario.")


@router.message(F.text.regexp(r"^\d+$"))
async def check_challenge_answer(message: Message, state: FSMContext):
    try:
        user_data = await state.get_data()

        # Verificar si hay un ejercicio activo (puede ser reto o ejercicio normal)
        if "current_exercise" not in user_data:
            await message.answer("❌ No hay reto activo. Usa /reto para empezar.")
            return

        exercise_data = user_data["current_exercise"]
        selected_option = int(message.text) - 1  # Convertir a índice 0-based

        # Validar que la opción seleccionada esté en el rango
        if selected_option < 0 or selected_option >= len(exercise_data["opciones"]):
            await message.answer(f"❌ Por favor, selecciona una opción entre 1 y {len(exercise_data['opciones'])}.")
            return

        # Usar la MISMA lógica compartida que los ejercicios normales
        result = await verify_answer_logic(
            message=message,
            state=state,
            selected_answer=selected_option,
            exercise_data=exercise_data,
            context="challenge" if user_data.get("is_challenge") else "exercise"
        )

        # MISMO COMPORTAMIENTO que en ejercicios normales
        if result["is_correct"]:
            # Mensaje de éxito personalizado para retos
            if user_data.get("is_challenge"):
                challenge_level = user_data.get("challenge_level", "desconocido").upper()
                await message.answer(
                    f"✅ **¡Correcto!** +1 punto\n\n"
                    f"💡 **Explicación:** {result['explanation']}\n\n"
                    f"🏅 ¡Has superado un reto de nivel {challenge_level}!",
                    reply_markup=result_keyboard(is_correct=True),
                    parse_mode="Markdown"
                )
            else:
                await message.answer(
                    f"✅ **¡Correcto!** +1 punto\n\n"
                    f"💡 **Explicación:** {result['explanation']}",
                    reply_markup=result_keyboard(is_correct=True),
                    parse_mode="Markdown"
                )
            await state.clear()

        else:
            # Manejo de intentos fallidos (MISMO que ejercicios normales)
            remaining_attempts = 3 - result["attempts"]

            if result["max_attempts_reached"]:
                await message.answer(
                    f"❌ **La respuesta correcta era:** {result['correct_answer']}\n\n"
                    f"💡 **Explicación:** {result['explanation']}",
                    reply_markup=result_keyboard(is_correct=False),
                    parse_mode="Markdown"
                )
                await state.clear()
            else:
                await message.answer(
                    f"❌ Incorrecto. Te quedan {remaining_attempts} intento(s).",
                    parse_mode="Markdown"
                )

    except Exception as e:
        logger.error(f"Error en check_challenge_answer: {e}")
        await message.answer("❌ Ocurrió un error al verificar tu respuesta.")