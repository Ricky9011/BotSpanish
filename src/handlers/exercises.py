from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.services.database_service import DatabaseService
from src.services.user_service import UserService
from src.keyboards.inline import exercise_keyboard, retry_keyboard
from src.utils.helpers import sanitize_text

router = Router()


@router.message(Command("ejercicio"))
@router.message(F.text == "📝 Ejercicio")
async def cmd_ejercicio(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Obtener nivel del usuario
    user_level = UserService.get_user_level(user_id)

    # Obtener ejercicios completados
    completed_exercises = UserService.get_completed_exercises(user_id)

    # Obtener ejercicio aleatorio
    exercise = DatabaseService.get_random_exercise(user_level, completed_exercises)

    if not exercise:
        await message.answer("🎉 ¡Has completado todos los ejercicios de tu nivel! Prueba con un nivel más avanzado.")
        return

    # Formatear mensaje
    message_text = (
        f"📚 *Ejercicio de {exercise.categoria} ({exercise.nivel})*\n\n"
        f"{exercise.pregunta}\n\n"
    )

    for idx, opcion in enumerate(exercise.opciones):
        message_text += f"{idx + 1}. {sanitize_text(opcion)}\n"

    # Guardar en estado
    await state.update_data(
        current_exercise=exercise.to_dict(),
        attempts=0
    )

    await message.answer(message_text, parse_mode="Markdown")


@router.callback_query(F.data == "next_exercise")
async def next_exercise(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await cmd_ejercicio(callback.message, state)


@router.callback_query(F.data == "retry_exercise")
async def retry_exercise(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    exercise_data = data.get("current_exercise")

    if not exercise_data:
        await callback.answer("No hay ejercicio activo")
        return

    exercise = Exercise(**exercise_data)
    message_text = (
        f"📚 *Ejercicio de {exercise.categoria} ({exercise.nivel})*\n\n"
        f"{exercise.pregunta}\n\n"
    )

    for idx, opcion in enumerate(exercise.opciones):
        message_text += f"{idx + 1}. {sanitize_text(opcion)}\n"

    await callback.message.edit_text(message_text, parse_mode="Markdown")
    await callback.answer()