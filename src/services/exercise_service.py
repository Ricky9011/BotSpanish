import json
from typing import Optional
from src.services.database import DatabaseService
from src.models.exercise import Exercise
from src.services.user_service import UserService

class ExerciseService:
    @classmethod
    def get_random_exercise(cls, user_id: int, nivel: str) -> Optional[Exercise]:
        completed_exercises = UserService.get_completed_exercises(user_id)
        with DatabaseService.get_cursor() as cursor:
            query = """
                SELECT id, categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion
                FROM ejercicios
                WHERE nivel = %s AND activo = TRUE
            """
            params = [nivel]

            if completed_exercises:
                query += " AND id NOT IN %s"
                params.append(tuple(completed_exercises))

            query += " ORDER BY RANDOM() LIMIT 1"

            cursor.execute(query, params)
            result = cursor.fetchone()

            if result:
                opciones = json.loads(result[4]) if isinstance(result[4], str) else result[4]
                return Exercise(
                    id=result[0],
                    categoria=result[1],
                    nivel=result[2],
                    pregunta=result[3],
                    opciones=opciones,
                    respuesta_correcta=result[5],
                    explicacion=result[6]
                )
            return None

    @classmethod
    def mark_exercise_completed(cls, user_id: int, exercise_id: int) -> None:
        completed_exercises = UserService.get_completed_exercises(user_id)
        if exercise_id not in completed_exercises:
            completed_exercises.append(exercise_id)
            completed_exercises_str = ",".join(str(x) for x in completed_exercises)
            with DatabaseService.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE users
                    SET completed_exercises = %s
                    WHERE user_id = %s
                """, (completed_exercises_str, user_id))