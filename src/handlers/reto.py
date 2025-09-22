from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.services.database import DatabaseService
from src.services.exercise_service import ExerciseService
from src.keyboards.inline import exercise_keyboard, retry_keyboard
import json

# Crear un enrutador para manejar comandos y mensajes relacionados con el reto diario
router = Router()

def format_exercise_message(exercise):
    """
    Formatea el mensaje del reto diario con las opciones disponibles.

    Args:
        exercise (dict): Diccionario que contiene los datos del ejercicio, incluyendo
                         la pregunta y las opciones.

    Returns:
        str: Mensaje formateado con la pregunta y las opciones enumeradas.
    """
    message_text = f"🏆 *Reto Diario*\n\n{exercise['pregunta']}\n\n"
    for idx, opcion in enumerate(exercise['opciones']):
        message_text += f"{idx + 1}. {opcion}\n"
    return message_text

async def handle_no_challenge(message):
    """
    Envía un mensaje al usuario indicando que no hay retos disponibles.

    Args:
        message (Message): Objeto del mensaje recibido.
    """
    await message.answer("❌ No hay retos disponibles en este momento.")

@router.message(Command("reto"))
@router.callback_query(F.data == "daily_challenge")
async def daily_challenge(message: Message | CallbackQuery, state: FSMContext):
    """
    Maneja el comando "/reto" o la interacción con el botón "daily_challenge".

    Args:
        message (Message | CallbackQuery): Mensaje o consulta de callback recibido.
        state (FSMContext): Contexto de la máquina de estados para almacenar datos temporales.

    Obtiene un ejercicio aleatorio de la base de datos, lo guarda en el estado del usuario
    y envía el reto al usuario.
    """
    if isinstance(message, CallbackQuery):
        message = message.message

    user_id = message.from_user.id

    # Obtener un ejercicio especial para el reto diario
    with DatabaseService.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion
            FROM ejercicios
            WHERE nivel = 'intermedio' AND categoria = 'gramática'
            ORDER BY RANDOM() LIMIT 1
        """)
        exercise_tuple = cursor.fetchone()

    if not exercise_tuple:
        await handle_no_challenge(message)
        return

    # Convertir la tupla obtenida en un diccionario
    exercise = dict(zip(
        ['id', 'categoria', 'nivel', 'pregunta', 'opciones', 'respuesta_correcta', 'explicacion'],
        exercise_tuple
    ))

    # Convertir las opciones de JSON string a lista si es necesario
    if isinstance(exercise['opciones'], str):
        try:
            exercise['opciones'] = json.loads(exercise['opciones'])
        except json.JSONDecodeError:
            pass

    # Guardar los datos del reto en el estado del usuario
    await state.update_data({
        "current_challenge": exercise,
        "challenge_attempts": 0,
        "challenge_id": exercise['id'],
        "challenge_nivel": exercise['nivel'],
        "challenge_categoria": exercise['categoria']
    })

    # Enviar el mensaje del reto al usuario
    await message.answer(format_exercise_message(exercise), parse_mode="Markdown")

@router.message(F.text.regexp(r"^\d+$"))
async def check_challenge_answer(message: Message, state: FSMContext):
    """
    Verifica la respuesta del usuario al reto diario.

    Args:
        message (Message): Mensaje recibido con la respuesta del usuario.
        state (FSMContext): Contexto de la máquina de estados para acceder a los datos del reto.

    Valida si la respuesta es correcta, actualiza el progreso del usuario y envía
    un mensaje de confirmación o error según corresponda.
    """
    user_id = message.from_user.id
    user_data = await state.get_data()

    if "current_challenge" not in user_data:
        await message.answer("❌ No hay reto activo. Usa /reto para empezar.", parse_mode="Markdown")
        return

    challenge_data = user_data["current_challenge"]
    selected_option = int(message.text) - 1

    if selected_option == challenge_data["respuesta_correcta"]:
        # Marcar el ejercicio como completado
        ExerciseService.mark_exercise_completed(
            user_id=user_id,
            exercise_id=user_data["challenge_id"],
            nivel=user_data["challenge_nivel"],
            categoria=user_data["challenge_categoria"]
        )

        # Obtener una curiosidad aleatoria
        curiosity = DatabaseService.get_random_curiosity()
        curiosity_text = curiosity.texto if curiosity else "¡Sigue practicando para aprender más curiosidades!"

        # Enviar mensaje de éxito al usuario
        await message.answer(
            "✅ ¡Correcto! +1 punto en el reto diario\n\n"
            f"💡 **Curiosidad:** {curiosity_text}\n\n"
            "¿Quieres intentar con otro reto?",
            reply_markup=exercise_keyboard(),
            parse_mode="Markdown"
        )
        await state.clear()
    else:
        # Incrementar el contador de intentos
        attempts = user_data.get("challenge_attempts", 0) + 1
        await state.update_data({"challenge_attempts": attempts})

        if attempts >= 3:
            # Enviar mensaje de error después de 3 intentos fallidos
            await message.answer(
                f"❌ La respuesta correcta era: {challenge_data['opciones'][challenge_data['respuesta_correcta']]}\n\n"
                "¿Quieres intentar con otro reto?",
                reply_markup=retry_keyboard(),
                parse_mode="Markdown"
            )
            await state.clear()
        else:
            # Permitir al usuario intentar nuevamente
            await message.answer(
                f"❌ Incorrecto. Te quedan {3 - attempts} intentos. Intenta nuevamente:",
                parse_mode="Markdown"
            )
