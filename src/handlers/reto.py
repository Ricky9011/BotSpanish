from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.services.database import DatabaseService
from src.services.exercise_service import ExerciseService
from src.services.user_service import UserService
from src.keyboards.inline import exercise_keyboard, retry_keyboard
import json

router = Router()


@router.message(Command("reto"))
@router.callback_query(F.data == "daily_challenge")
async def daily_challenge(message: Message | CallbackQuery, state: FSMContext):
    if isinstance(message, CallbackQuery):
        message = message.message

    user_id = message.from_user.id

    # Obtener un ejercicio especial para el reto
    with DatabaseService.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion
            FROM ejercicios 
            WHERE nivel = 'intermedio' 
            AND categoria = 'gramática'
            ORDER BY RANDOM() 
            LIMIT 1
        """)
        exercise_tuple = cursor.fetchone()

    if exercise_tuple:
        # Convertir la tupla a un diccionario
        exercise = {
            'id': exercise_tuple[0],
            'categoria': exercise_tuple[1],
            'nivel': exercise_tuple[2],
            'pregunta': exercise_tuple[3],
            'opciones': exercise_tuple[4],
            'respuesta_correcta': exercise_tuple[5],
            'explicacion': exercise_tuple[6]
        }

        # Convertir opciones de JSON string a lista si es necesario
        if isinstance(exercise['opciones'], str):
            try:
                exercise['opciones'] = json.loads(exercise['opciones'])
            except json.JSONDecodeError:
                # Si no es JSON válido, mantener el valor original
                pass

        # Guardar en estado con toda la información necesaria
        await state.update_data({
            "current_challenge": exercise,
            "challenge_attempts": 0,
            "challenge_id": exercise['id'],
            "challenge_nivel": exercise['nivel'],
            "challenge_categoria": exercise['categoria']
        })

        # Formatear mensaje
        message_text = f"🏆 *Reto Diario*\n\n{exercise['pregunta']}\n\n"

        for idx, opcion in enumerate(exercise['opciones']):
            message_text += f"{idx + 1}. {opcion}\n"  # Mostrar opciones 1, 2, 3, 4

        await message.answer(message_text, parse_mode="Markdown")
    else:
        await message.answer("❌ No hay retos disponibles en este momento.")


@router.message(F.text.regexp(r"^\d+$"))
async def check_challenge_answer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await state.get_data()

    # Verificar si hay un reto activo
    if "current_challenge" not in user_data:
        await message.answer("❌ No hay reto activo. Usa /reto para empezar.", parse_mode="Markdown")
        return

    challenge_data = user_data["current_challenge"]

    # El usuario ingresa 1, 2, 3, 4 pero la BD almacena 0, 1, 2, 3
    selected_option = int(message.text) - 1  # Convertir a índice 0-based

    # Verificar respuesta
    if selected_option == challenge_data["respuesta_correcta"]:
        # Respuesta correcta - registrar en la nueva tabla user_ejercicios
        ExerciseService.mark_exercise_completed(
            user_id=user_id,
            exercise_id=user_data["challenge_id"],
            nivel=user_data["challenge_nivel"],
            categoria=user_data["challenge_categoria"]
        )

        # Obtener una curiosidad aleatoria
        curiosity_obj = DatabaseService.get_random_curiosity()
        if curiosity_obj:
            curiosity_text = curiosity_obj.texto
        else:
            curiosity_text = "¡Sigue practicando para aprender más curiosidades!"

        # Mensaje de éxito
        await message.answer(
            "✅ ¡Correcto! +1 punto en el reto diario\n\n"
            f"💡 **Curiosidad:** {curiosity_text}\n\n"
            "¿Quieres intentar con otro reto?",
            reply_markup=exercise_keyboard(),
            parse_mode="Markdown"
        )

        # Limpiar el estado del reto
        await state.clear()
    else:
        # Respuesta incorrecta
        attempts = user_data.get("challenge_attempts", 0) + 1
        await state.update_data({"challenge_attempts": attempts})

        if attempts >= 3:
            await message.answer(
                f"❌ La respuesta correcta era: {challenge_data['opciones'][challenge_data['respuesta_correcta']]}\n\n"
                "¿Quieres intentar con otro reto?",
                reply_markup=retry_keyboard(),
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            await message.answer(
                f"❌ Incorrecto. Te quedan {3 - attempts} intentos. Intenta nuevamente:",
                parse_mode="Markdown"
            )