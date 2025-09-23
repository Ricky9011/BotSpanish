# handlers/exercises.py - CON TECLADO DE OPCIONES
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from src.keyboards.main_menu import MainMenuKeyboard
from src.services.user_service import UserService
from src.services.exercise_service import ExerciseService
from src.keyboards.inline import exercise_keyboard, retry_keyboard
import json
import logging

logger = logging.getLogger(__name__)
router = Router(name="exercises")


def create_answer_keyboard(options: list) -> ReplyKeyboardMarkup:
    """Crea un teclado con las opciones de respuesta"""
    builder = ReplyKeyboardBuilder()

    # Agregar cada opción como botón
    for option in options:
        builder.add(KeyboardButton(text=option))

    # Ajustar disposición (2 columnas)
    builder.adjust(2)

    # Agregar botón de cancelar
    builder.row(KeyboardButton(text="❌ Cancelar ejercicio"))

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True  # El teclado se oculta después de usar
    )


@router.message(Command("ejercicio"))
@router.message(F.text == "📝 Ejercicio")
async def cmd_exercise(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_level = UserService.get_user_level(user_id)

    exercise = ExerciseService.get_random_exercise(user_id, user_level)

    if not exercise:
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
                reply_markup=MainMenuKeyboard.main_menu(),
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

    if isinstance(exercise.opciones, str):
        try:
            exercise.opciones = json.loads(exercise.opciones)
        except json.JSONDecodeError:
            exercise.opciones = [exercise.opciones]

    message_text = (
        f"📚 *Ejercicio de {exercise.categoria} ({exercise.nivel})*\n\n"
        f"{exercise.pregunta}\n\n"
        "💡 **Selecciona tu respuesta:**"
    )

    # Crear teclado con opciones
    answer_keyboard = create_answer_keyboard(exercise.opciones)

    await state.update_data({
        "current_exercise": exercise.to_dict(),
        "attempts": 0,
        "exercise_id": exercise.id,
        "exercise_nivel": exercise.nivel,
        "exercise_categoria": exercise.categoria,
        "answer_options": exercise.opciones  # Guardar opciones para validar
    })

    await message.answer(message_text, parse_mode="Markdown", reply_markup=answer_keyboard)


@router.message(F.text == "❌ Cancelar ejercicio")
async def cancel_exercise(message: Message, state: FSMContext):
    """Cancelar el ejercicio actual y volver al menú principal"""
    await state.clear()
    await message.answer(
        "❌ Ejercicio cancelado.",
        reply_markup=MainMenuKeyboard.main_menu()
    )


@router.message(F.text)
async def handle_text_answer(message: Message, state: FSMContext):
    """Manejar respuestas de texto (selección de opciones)"""
    user_id = message.from_user.id
    user_data = await state.get_data()

    # Verificar si hay un ejercicio activo
    if "current_exercise" not in user_data:
        # Si no hay ejercicio activo, ignorar o mostrar mensaje
        return

    # Obtener las opciones de respuesta
    answer_options = user_data.get("answer_options", [])
    selected_text = message.text

    # Verificar si el texto seleccionado es una de las opciones válidas
    if selected_text not in answer_options:
        await message.answer("❌ Por favor, selecciona una de las opciones proporcionadas.")
        return

    # Encontrar el índice de la opción seleccionada
    selected_option = answer_options.index(selected_text)
    exercise_data = user_data["current_exercise"]
    attempts = user_data.get("attempts", 0) + 1

    is_correct = selected_option == exercise_data["respuesta_correcta"]

    if is_correct:
        ExerciseService.mark_exercise_completed(
            user_id=user_id,
            exercise_id=user_data["exercise_id"],
            nivel=user_data["exercise_nivel"],
            categoria=user_data["exercise_categoria"],
            is_correct=True,
            attempts=attempts
        )

        explanation = exercise_data.get('explicacion', '¡Excelente trabajo! Has acertado la respuesta.')

        await message.answer(
            f"✅ **¡Correcto!** +1 punto\n\n"
            f"💡 **Explicación:** {explanation}\n\n"
            "¿Quieres continuar practicando?",
            reply_markup=exercise_keyboard(),
            parse_mode="Markdown"
        )
        await state.clear()
    else:
        await state.update_data({"attempts": attempts})

        if attempts >= 3:
            correct_answer = answer_options[exercise_data["respuesta_correcta"]]
            explanation = exercise_data.get('explicacion', 'Sigue practicando para mejorar.')

            await message.answer(
                f"❌ **La respuesta correcta era:** {correct_answer}\n\n"
                f"💡 **Explicación:** {explanation}\n\n"
                "¿Quieres intentar con otro ejercicio?",
                reply_markup=retry_keyboard(),
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            await message.answer(
                f"❌ Incorrecto. Intenta nuevamente (intento {attempts}/3):",
                reply_markup=create_answer_keyboard(answer_options)  # Mostrar opciones nuevamente
            )


# Mantener los callbacks para inline keyboard (siguiente ejercicio, reintentar, etc.)
@router.callback_query(F.data == "next_exercise")
async def next_exercise(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_exercise(callback.message, state)
    await callback.message.delete()


@router.callback_query(F.data == "retry_exercise")
async def retry_exercise(callback: CallbackQuery, state: FSMContext):
    await cmd_exercise(callback.message, state)
    await callback.message.delete()


@router.callback_query(F.data == "show_progress")
async def show_progress_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = UserService.get_user_stats(user_id)

    if not stats:
        await callback.message.answer("❌ No se encontraron datos de progreso.")
        return

    progress_text = (
        f"📊 **Tu Progreso**\n\n"
        f"🏅 Nivel: {stats['level'].capitalize()}\n"
        f"✅ Ejercicios completados: {stats['exercises']}\n"
        f"👥 Referidos: {stats['referrals']}\n"
        f"🏆 Puntos de desafío: {stats['challenge_score']}\n"
        f"🔥 Racha actual: {stats['streak_days']} días\n"
    )

    if stats.get('exercises_by_level'):
        progress_text += "\n📈 **Por nivel:**\n"
        for nivel, count in stats['exercises_by_level'].items():
            progress_text += f"  - {nivel.capitalize()}: {count}\n"

    if stats.get('exercises_by_category'):
        progress_text += "\n📚 **Por categoría:**\n"
        for categoria, count in stats['exercises_by_category'].items():
            progress_text += f"  - {categoria.capitalize()}: {count}\n"

    if stats.get('last_practice'):
        progress_text += f"\n⏰ Última práctica: {stats['last_practice'].strftime('%Y-%m-%d %H:%M')}\n"

    await callback.message.answer(progress_text, parse_mode="Markdown")
    await callback.answer()