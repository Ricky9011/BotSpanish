# handlers/reto.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.services.database import DatabaseService
from src.keyboards.inline import exercise_keyboard, retry_keyboard
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

    user_id = message.from_user.id

    # Importar aquí para evitar circular import
    from src.services.user_service import UserService
    from src.services.exercise_service import ExerciseService

    # Obtener nivel del usuario y calcular nivel superior para el reto
    user_level = UserService.get_user_level(user_id)
    challenge_level = get_superior_level(user_level)

    # Obtener ejercicio del nivel superior que el usuario no haya completado
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
        "current_challenge": exercise.to_dict(),
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

    # Importar aquí para evitar circular import
    from src.services.exercise_service import ExerciseService

    challenge_data = user_data["current_challenge"]
    selected_option = int(message.text) - 1
    attempts = user_data.get("challenge_attempts", 0) + 1

    is_correct = selected_option == challenge_data["respuesta_correcta"]

    if is_correct:
        # Respuesta correcta - marcar como completado
        ExerciseService.mark_exercise_completed(
            user_id=user_id,
            exercise_id=user_data["challenge_id"],
            nivel=user_data["challenge_nivel"],
            categoria=user_data["challenge_categoria"],
            is_correct=True,
            attempts=attempts
        )

        # MOSTRAR EXPLICACIÓN
        explanation = challenge_data.get('explicacion', '¡Excelente trabajo! Has dominado este concepto.')

        success_message = (
            f"✅ **¡Correcto!** +1 punto\n\n"
            f"💡 **Explicación:** {explanation}\n\n"
            f"🏅 Has completado un reto de nivel {user_data['challenge_level'].upper()}!\n\n"
            "¿Quieres intentar otro reto?"
        )

        await message.answer(
            success_message,
            reply_markup=exercise_keyboard(),
            parse_mode="Markdown"
        )
        await state.clear()
    else:
        await state.update_data({"challenge_attempts": attempts})

        if attempts >= 3:
            # Mostrar respuesta correcta y explicación
            correct_answer = challenge_data['opciones'][challenge_data['respuesta_correcta']]
            explanation = challenge_data.get('explicacion', 'Sigue practicando para mejorar.')

            failure_message = (
                f"❌ **La respuesta correcta era:** {correct_answer}\n\n"
                f"💡 **Explicación:** {explanation}\n\n"
                "¿Quieres intentar con otro reto?"
            )

            await message.answer(
                failure_message,
                reply_markup=retry_keyboard(),
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            remaining_attempts = 3 - attempts
            await message.answer(
                f"❌ Incorrecto. Te quedan {remaining_attempts} intentos."
            )