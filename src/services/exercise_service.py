import random
from src.services.database import Database
from src.models.exercise import Exercise


class ExerciseService:
    @staticmethod
    def get_random_exercise(user_id: int, level: str) -> Exercise:
        with Database.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, categoria, pregunta, opciones, respuesta_correcta
                FROM ejercicios
                WHERE nivel = %s
                AND id NOT IN (
                    SELECT unnest(string_to_array(completed_exercises, ',')::INT)
                    FROM users WHERE user_id = %s
                )
                ORDER BY RANDOM()
                LIMIT 1
            """, (level, user_id))

            exercise_data = cursor.fetchone()

            if not exercise_data:
                # Reiniciar progreso y reintentar
                cursor.execute("UPDATE users SET completed_exercises = '' WHERE user_id = %s", (user_id,))
                cursor.execute("...")  # Misma query
                exercise_data = cursor.fetchone()

            return Exercise(*exercise_data)