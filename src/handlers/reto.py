# handlers/reto.py - VERSIÓN MEJORADA
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.services.answer_service import verify_answer_logic
from src.keyboards.inline import result_keyboard, exercise_keyboard
import json

router = Router(name="reto")

def get_superior_level(current_level: str) -> str:
    """Devuelve el nivel superior al actual"""
    levels = ["principiante", "intermedio", "avanzado"]
    try:
        current_index = levels.index(current_level)
        superior_index = min(current_index + 1, len(levels) - 1)
        return levels[superior_index]
    except ValueError:
        return "intermedio"

@router.message(Command("reto"))
@router.callback_query(F.data == "daily_challenge")
async def daily_challenge(message: Message | CallbackQuery, state: FSMContext):
    if isinstance(message, CallbackQuery):
        message = message.message
        await message.edit_reply_markup(reply_markup=None)  # Limpiar teclado anterior

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

    # Crear diccionario de datos del ejercicio
    challenge_data = {
        "id": exercise.id,
        "categoria": exercise.categoria,
        "nivel": exercise.nivel,
        "pregunta": exercise.pregunta,
        "opciones": exercise.opciones,
        "respuesta_correcta": exercise.respuesta_correcta,
        "explicacion": exercise.explicacion
    }

    # Formatear mensaje del reto
    message_text = (
        f"🏆 *Reto Diario - Nivel {challenge_level.upper()}*\n\n"
        f"📚 Categoría: {exercise.categoria}\n\n"
        f"{exercise.pregunta}\n\n"
    )

    for idx, opcion in enumerate(exercise.opciones):
        message_text += f"{idx + 1}. {opcion}\n"

    # Guardar en estado
    await state.update_data({
        "current_challenge": challenge_data,
        "challenge_attempts": 0,
        "challenge_id": exercise.id,
        "challenge_nivel": exercise.nivel,
        "challenge_categoria": exercise.categoria,
        "challenge_level": challenge_level
    })

    await message.answer(message_text, parse_mode="Markdown")

@router.message(F.text.regexp(r"^\d+$"))
async def check_challenge_answer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await state.get_data()

    if "current_challenge" not in user_data:
        await message.answer("❌ No hay reto activo. Usa /reto para empezar.")
        return

    challenge_data = user_data["current_challenge"]
    selected_option = int(message.text) - 1  # Convertir a índice 0-based

    # Usar la lógica compartida
    result = await verify_answer_logic(
        message=message,
        state=state,
        selected_answer=selected_option,
        exercise_data=challenge_data,
        context="challenge"
    )

    if result["is_correct"]:
        # Respuesta correcta
        await message.answer(
            f"✅ **¡Correcto!** +1 punto\n\n"
            f"💡 **Explicación:** {result['explanation']}\n\n"
            f"🏅 Has completado un reto de nivel {user_data['challenge_level'].upper()}!",
            reply_markup=result_keyboard(is_correct=True),
            parse_mode="Markdown"
        )
        await state.clear()
    else:
        await state.update_data({"challenge_attempts": result["attempts"]})

        if result["max_attempts_reached"]:
            # Máximos intentos alcanzados
            await message.answer(
                f"❌ **La respuesta correcta era:** {result['correct_answer']}\n\n"
                f"💡 **Explicación:** {result['explanation']}",
                reply_markup=result_keyboard(is_correct=False),
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            # Intentar nuevamente
            remaining_attempts = 3 - result["attempts"]
            await message.answer(f"❌ Incorrecto. Te quedan {remaining_attempts} intentos.")