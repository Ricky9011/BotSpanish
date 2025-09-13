from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from typing import Optional
from src.models.exercise import Exercise
from src.services.database import DatabaseService
from src.services.exercise_service import ExerciseService
from src.services.user_service import UserService
from src.keyboards.inline import exercise_keyboard, retry_keyboard
from src.handlers.progress import cmd_progress

router = Router()


@router.message(Command("ejercicio"))
@router.message(F.text == "📝 Ejercicio")
async def cmd_exercise(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Obtener nivel del usuario
    user_level = UserService.get_user_level(user_id)

    # Obtener ejercicio aleatorio
    exercise = ExerciseService.get_random_exercise(user_id, user_level)

    if not exercise:
        await message.answer("🎉 ¡Has completado todos los ejercicios de tu nivel!", parse_mode="Markdown")
        return

    # Formatear mensaje
    message_text = (
        f"📚 *Ejercicio de {exercise.categoria} ({exercise.nivel})*\n\n"
        f"{exercise.pregunta}\n\n"
    )

    for idx, opcion in enumerate(exercise.opciones):
        message_text += f"{idx + 1}. {opcion}\n"

    # Guardar en estado
    await state.update_data({
        "current_exercise": exercise.to_dict(),
        "attempts": 0
    })

    await message.answer(message_text, parse_mode="Markdown")


@router.message(F.text.regexp(r"^\d+$"))
async def check_answer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await state.get_data()

    # Verificar si hay un ejercicio activo
    if "current_exercise" not in user_data:
        await message.answer("❌ No hay ejercicio activo. Usa /ejercicio para empezar.", parse_mode="Markdown")
        return

    exercise_data = user_data["current_exercise"]
    selected_option = int(message.text) - 1

    # Verificar respuesta
    if selected_option == exercise_data["respuesta_correcta"]:
        # Respuesta correcta
        ExerciseService.mark_exercise_completed(user_id, exercise_data["id"])
        UserService.update_user_stats(user_id)

        # Mensaje de éxito
        await message.answer(
            "✅ ¡Correcto! +1 punto\n\n"
            "¿Quieres continuar practicando?",
            reply_markup=exercise_keyboard(),
            parse_mode="Markdown"
        )
    else:
        # Respuesta incorrecta
        attempts = user_data.get("attempts", 0) + 1
        await state.update_data({"attempts": attempts})

        if attempts >= 3:
            await message.answer(
                f"❌ La respuesta correcta era: {exercise_data['opciones'][exercise_data['respuesta_correcta']]}\n\n"
                "¿Quieres intentar con otro ejercicio?",
                reply_markup=retry_keyboard(),
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            await message.answer(
                "❌ Incorrecto. Intenta nuevamente:",
                reply_markup=retry_keyboard(),
                parse_mode="Markdown"
            )


@router.callback_query(F.data == "next_exercise")
async def next_exercise(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_exercise(callback.message, state)
    await callback.message.delete()


@router.callback_query(F.data == "retry_exercise")
async def retry_exercise(callback: CallbackQuery, state: FSMContext):
    await cmd_exercise(callback.message, state)
    await callback.message.delete()


@router.callback_query(F.data == "show_progress")  # Cambiado a "show_progress"
async def show_progress_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = UserService.get_user_stats(user_id)

    progress_text = (
        f"📊 **Tu Progreso**\n\n"
        f"🏅 Nivel: {stats['level'].capitalize()}\n"
        f"✅ Ejercicios completados: {stats['exercises']}\n"
        f"👥 Referidos: {stats['referrals']}\n"
        f"🏆 Puntos de desafío: {stats['challenge_score']}\n"
        f"🔥 Racha actual: {stats['streak_days']} días\n"
    )

    if stats['last_practice']:
        progress_text += f"⏰ Última práctica: {stats['last_practice'].strftime('%Y-%m-%d %H:%M')}\n"

    await callback.message.answer(progress_text, parse_mode="Markdown")
    await callback.answer()