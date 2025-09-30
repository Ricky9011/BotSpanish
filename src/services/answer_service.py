# src/services/answer_service.py
import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.services.exercise_service import ExerciseService

logger = logging.getLogger(__name__)


async def verify_answer_logic(
        message: Message,
        state: FSMContext,
        selected_answer: int,
        exercise_data: dict,
        context: str = "exercise"
) -> dict:
    """
    Lógica compartida para verificar respuestas
    Retorna un dict con los resultados sin enviar mensajes
    """
    user_id = message.from_user.id
    user_data = await state.get_data()

    # Determinar IDs según contexto
    exercise_id = user_data.get("current_exercise_id") or user_data.get("challenge_id")
    attempts = user_data.get("attempts", 0) + 1

    # Verificar si es correcta
    is_correct = selected_answer == exercise_data["respuesta_correcta"]

    # Marcar como completado
    success = ExerciseService.mark_exercise_completed(
        user_id=user_id,
        exercise_id=exercise_id,
        nivel=exercise_data["nivel"],
        categoria=exercise_data["categoria"],
        is_correct=is_correct,
        attempts=attempts
    )

    return {
        "is_correct": is_correct,
        "attempts": attempts,
        "success": success,
        "max_attempts_reached": attempts >= 3,
        "explanation": exercise_data.get('explicacion', '¡Excelente trabajo!'),
        "correct_answer": exercise_data['opciones'][exercise_data['respuesta_correcta']] if not is_correct else None
    }