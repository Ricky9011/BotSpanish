# services/exercise_service.py - VERSIÓN CORREGIDA
import logging
from typing import List, Optional
from src.services.database import DatabaseService
from src.models.exercise import Exercise
import json

logger = logging.getLogger(__name__)


class ExerciseService:

    @staticmethod
    def get_random_exercise(user_id: int, nivel: str) -> Optional[Exercise]:
        """Obtiene un ejercicio aleatorio que el usuario NO haya completado"""
        try:
            # Obtener IDs de ejercicios ya completados por el usuario
            completed_exercise_ids = ExerciseService.get_completed_exercise_ids(user_id)

            # Usar DatabaseService para obtener ejercicio aleatorio excluyendo completados
            with DatabaseService.get_cursor() as cursor:
                query = """
                    SELECT id, categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion
                    FROM ejercicios 
                    WHERE nivel = %s AND activo = TRUE
                """
                params = [nivel]

                if completed_exercise_ids:
                    # Crear placeholders para los IDs excluidos
                    placeholders = ','.join(['%s'] * len(completed_exercise_ids))
                    query += f" AND id NOT IN ({placeholders})"
                    params.extend(completed_exercise_ids)

                query += " ORDER BY RANDOM() LIMIT 1"

                cursor.execute(query, params)
                result = cursor.fetchone()

                if result:
                    # Convertir resultado a objeto Exercise
                    return Exercise(
                        id=result[0],
                        categoria=result[1],
                        nivel=result[2],
                        pregunta=result[3],
                        opciones=result[4],
                        respuesta_correcta=result[5],
                        explicacion=result[6]
                    )
                return None

        except Exception as e:
            logger.error(f"Error al obtener ejercicio aleatorio: {e}")
            return None

    @staticmethod
    def get_completed_exercise_ids(user_id: int) -> List[int]:
        """Obtiene la lista de IDs de ejercicios completados por el usuario"""
        try:
            with DatabaseService.get_cursor() as cursor:
                cursor.execute(
                    "SELECT exercise_id FROM user_ejercicios WHERE user_id = %s",
                    (user_id,)
                )
                results = cursor.fetchall()
                return [row[0] for row in results] if results else []
        except Exception as e:
            logger.error(f"Error al obtener ejercicios completados: {e}")
            return []

    @staticmethod
    def mark_exercise_completed(user_id: int, exercise_id: int, nivel: str,
                                categoria: str, is_correct: bool, attempts: int) -> bool:
        """Marca un ejercicio como completado usando UPSERT para evitar duplicados"""
        try:
            with DatabaseService.get_cursor() as cursor:
                # Verificar si ya existe el registro
                cursor.execute(
                    "SELECT * FROM user_ejercicios WHERE user_id = %s AND exercise_id = %s",
                    (user_id, exercise_id)
                )
                existing_record = cursor.fetchone()

                if existing_record:
                    # Actualizar registro existente
                    cursor.execute("""
                        UPDATE user_ejercicios 
                        SET is_correct = %s, attempts = %s, nivel = %s, categoria = %s, completed_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s AND exercise_id = %s
                    """, (is_correct, attempts, nivel, categoria, user_id, exercise_id))
                    logger.info(f"Actualizado ejercicio {exercise_id} para usuario {user_id}")
                else:
                    # Crear nuevo registro
                    cursor.execute("""
                        INSERT INTO user_ejercicios (user_id, exercise_id, nivel, categoria, is_correct, attempts, completed_at)
                        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """, (user_id, exercise_id, nivel, categoria, is_correct, attempts))
                    logger.info(f"Marcado ejercicio {exercise_id} como completado para usuario {user_id}")

                return True

        except Exception as e:
            logger.error(f"Error al marcar ejercicio como completado: {e}")
            return False

    @staticmethod
    def get_available_exercises_count(user_id: int, nivel: str) -> int:
        """Cuenta cuántos ejercicios disponibles hay para un usuario en un nivel"""
        try:
            completed_exercise_ids = ExerciseService.get_completed_exercise_ids(user_id)

            with DatabaseService.get_cursor() as cursor:
                query = "SELECT COUNT(*) FROM ejercicios WHERE nivel = %s AND activo = TRUE"
                params = [nivel]

                if completed_exercise_ids:
                    placeholders = ','.join(['%s'] * len(completed_exercise_ids))
                    query += f" AND id NOT IN ({placeholders})"
                    params.extend(completed_exercise_ids)

                cursor.execute(query, params)
                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"Error al contar ejercicios disponibles: {e}")
            return 0

    # exercise_service.py - Añadir método de estadísticas
    @staticmethod
    def get_user_stats(user_id: int) -> dict:
        """Obtiene estadísticas del usuario"""
        try:
            # Implementación básica - ajusta según tu base de datos
            with DatabaseService.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN is_correct THEN 1 END) as correct,
                        COUNT(DISTINCT categoria) as categories,
                        COUNT(DISTINCT nivel) as levels
                    FROM user_ejercicios 
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()

                return {
                    'total_exercises': result[0] if result else 0,
                    'correct_exercises': result[1] if result else 0,
                    'categories_count': result[2] if result else 0,
                    'levels_count': result[3] if result else 0
                }
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {}