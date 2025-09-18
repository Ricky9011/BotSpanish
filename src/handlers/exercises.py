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

router = Router()


@router.message(Command("ejercicio"))
@router.message(F.text == "📝 Ejercicio")
async def cmd_exercise(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Obtener nivel del usuario
    user_level = UserService.get_user_level(user_id)

    # Obtener ejercicio aleatorio no completado
    exercise = ExerciseService.get_random_exercise(user_id, user_level)

    if not exercise:
        # Verificar si hay ejercicios de otros niveles
        all_levels = ["principiante", "intermedio", "avanzado"]
        other_levels = [lvl for lvl in all_levels if lvl != user_level]

        alternative_exercise = None
        alternative_level = None

        for level in other_levels:
            alternative_exercise = ExerciseService.get_random_exercise(user_id, level)
            if alternative_exercise:
                alternative_level = level
                break

        if not alternative_exercise:
            await message.answer(
                "🎉 ¡Felicidades! Has completado todos los ejercicios disponibles.\n\n"
                "Pronto añadiremos más contenido. ¡Mantente atento!",
                parse_mode="Markdown"
            )
            return
        else:
            await message.answer(
                f"🎯 ¡Has completado todos los ejercicios de tu nivel ({user_level})! "
                f"Te mostramos un ejercicio del nivel {alternative_level}:",
                parse_mode="Markdown"
            )
            exercise = alternative_exercise

    # Formatear mensaje
    message_text = (
        f"📚 *Ejercicio de {exercise.categoria} ({exercise.nivel})*\n\n"
        f"{exercise.pregunta}\n\n"
    )

    for idx, opcion in enumerate(exercise.opciones):
        message_text += f"{idx + 1}. {opcion}\n"

    # Guardar en estado con toda la información necesaria
    await state.update_data({
        "current_exercise": exercise.to_dict(),
        "attempts": 0,
        "exercise_id": exercise.id,
        "exercise_nivel": exercise.nivel,
        "exercise_categoria": exercise.categoria
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
        # Respuesta correcta - usar la nueva tabla user_ejercicios
        ExerciseService.mark_exercise_completed(
            user_id=user_id,
            exercise_id=user_data["exercise_id"],
            nivel=user_data["exercise_nivel"],
            categoria=user_data["exercise_categoria"]
        )

        # Obtener una curiosidad aleatoria
        curiosity_obj = DatabaseService.get_random_curiosity()
        if curiosity_obj:
            curiosity_text = curiosity_obj.texto
        else:
            curiosity_text = "¡Sigue practicando para aprender más curiosidades!"

        # Mensaje de éxito
        await message.answer(
            "✅ ¡Correcto! +1 punto\n\n"
            f"💡 **Curiosidad:** {curiosity_text}\n\n"
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


# exercises.py - En el callback show_progress_callback
@router.callback_query(F.data == "show_progress")
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

    # Añadir estadísticas por nivel si existen
    if stats['exercises_by_level']:
        progress_text += "\n📈 **Por nivel:**\n"
        for nivel, count in stats['exercises_by_level'].items():
            progress_text += f"  - {nivel.capitalize()}: {count}\n"

    # Añadir estadísticas por categoría si existen
    if stats['exercises_by_category']:
        progress_text += "\n📚 **Por categoría:**\n"
        for categoria, count in stats['exercises_by_category'].items():
            progress_text += f"  - {categoria.capitalize()}: {count}\n"

    if stats['last_practice']:
        progress_text += f"\n⏰ Última práctica: {stats['last_practice'].strftime('%Y-%m-%d %H:%M')}\n"

    await callback.message.answer(progress_text, parse_mode="Markdown")
    await callback.answer()