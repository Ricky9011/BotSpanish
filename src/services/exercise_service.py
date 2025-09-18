from typing import Optional, List
from src.services.database import DatabaseService
from src.models.exercise import Exercise

class ExerciseService:
    # En src/services/exercise_service.py
    @staticmethod
    def mark_exercise_completed(user_id: int, exercise_id: int, nivel: str, categoria: str):
        """
        Marca un ejercicio como completado por un usuario en la nueva tabla
        """
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_ejercicios (user_id, exercise_id, nivel, categoria)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, exercise_id) DO NOTHING
            """, (user_id, exercise_id, nivel, categoria))

    @staticmethod
    def get_completed_exercises(user_id: int) -> List[int]:
        """
        Obtiene la lista de IDs de ejercicios completados por el usuario
        """
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                SELECT exercise_id FROM user_ejercicios WHERE user_id = %s
            """, (user_id,))

            results = cursor.fetchall()
            return [result[0] for result in results] if results else []

    @classmethod
    def get_random_exercise(cls, user_id: int, user_level: str) -> Optional[Exercise]:
        """
        Obtiene un ejercicio aleatorio que el usuario no haya completado
        """
        completed_exercises = cls.get_completed_exercises(user_id)

        with DatabaseService.get_cursor() as cursor:
            if completed_exercises:
                cursor.execute("""
                    SELECT id, categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion
                    FROM ejercicios 
                    WHERE nivel = %s 
                    AND activo = TRUE 
                    AND id NOT IN %s
                    ORDER BY RANDOM() 
                    LIMIT 1
                """, (user_level, tuple(completed_exercises)))
            else:
                cursor.execute("""
                    SELECT id, categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion
                    FROM ejercicios 
                    WHERE nivel = %s 
                    AND activo = TRUE 
                    ORDER BY RANDOM() 
                    LIMIT 1
                """, (user_level,))

            result = cursor.fetchone()
            if result:
                # Convertir opciones a lista si es necesario
                opciones = result[4]
                if isinstance(opciones, str):
                    try:
                        # Intentar parsear como JSON
                        import json
                        opciones = json.loads(opciones)
                    except (json.JSONDecodeError, TypeError):
                        # Si falla, tratar como cadena separada por comas
                        opciones = [opc.strip() for opc in opciones.split(',')]

                # Crear una nueva tupla con las opciones convertidas
                modified_result = (
                    result[0],  # id
                    result[1],  # categoria
                    result[2],  # nivel
                    result[3],  # pregunta
                    opciones,  # opciones (convertida a lista)
                    result[5],  # respuesta_correcta
                    result[6]  # explicacion
                )

                return Exercise(*modified_result)
            return None
  
    @staticmethod
    def get_user_exercise_stats(user_id: int) -> dict:
        """
        Obtiene estadísticas detalladas de ejercicios completados por el usuario
        """
        with DatabaseService.get_cursor() as cursor:
            # Total de ejercicios completados
            cursor.execute("""
                SELECT COUNT(*) FROM user_ejercicios WHERE user_id = %s
            """, (user_id,))
            total_completed = cursor.fetchone()[0]

            # Ejercicios completados por nivel
            cursor.execute("""
                SELECT nivel, COUNT(*) 
                FROM user_ejercicios 
                WHERE user_id = %s 
                GROUP BY nivel
            """, (user_id,))
            by_level = {row[0]: row[1] for row in cursor.fetchall()}

            # Ejercicios completados por categoría
            cursor.execute("""
                SELECT categoria, COUNT(*) 
                FROM user_ejercicios 
                WHERE user_id = %s 
                GROUP BY categoria
            """, (user_id,))
            by_category = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'total_completed': total_completed,
                'by_level': by_level,
                'by_category': by_category
            }