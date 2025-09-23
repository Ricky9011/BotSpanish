# services/exercise_service.py - Versión mejorada
from src.services.database import DatabaseService
import logging

logger = logging.getLogger(__name__)


class ExerciseService:
    @staticmethod
    def mark_exercise_completed(user_id: int, exercise_id: int, nivel: str, categoria: str, is_correct: bool = True,
                                attempts: int = 1):
        """Marca un ejercicio como completado en user_ejercicios"""
        try:
            with DatabaseService.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_ejercicios (user_id, exercise_id, nivel, categoria, is_correct, attempts)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, exercise_id, nivel, categoria, is_correct, attempts))
                logger.info(f"Ejercicio {exercise_id} marcado como completado para usuario {user_id}")
        except Exception as e:
            logger.error(f"Error al marcar ejercicio como completado: {e}")
            # Intentar con una estructura de tabla alternativa si falla
            try:
                with DatabaseService.get_cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO user_ejercicios (user_id, exercise_id, nivel, categoria, is_correct)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, exercise_id, nivel, categoria, is_correct))
            except Exception as e2:
                logger.error(f"Error alternativo también falló: {e2}")

    @staticmethod
    def get_random_exercise(user_id: int, user_level: str):
        """Obtiene un ejercicio aleatorio que el usuario no haya completado correctamente"""
        try:
            with DatabaseService.get_cursor() as cursor:
                # Primero verificar si la tabla user_ejercicios existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'user_ejercicios'
                    );
                """)
                table_exists = cursor.fetchone()[0]

                if table_exists:
                    # Usar la nueva tabla si existe
                    cursor.execute("""
                        SELECT e.id, e.categoria, e.nivel, e.pregunta, e.opciones, e.respuesta_correcta, e.explicacion
                        FROM ejercicios e
                        WHERE e.nivel = %s 
                        AND e.activo = true
                        AND e.id NOT IN (
                            SELECT ue.exercise_id 
                            FROM user_ejercicios ue 
                            WHERE ue.user_id = %s AND ue.is_correct = true
                        )
                        ORDER BY RANDOM()
                        LIMIT 1
                    """, (user_level, user_id))
                else:
                    # Fallback a la lógica antigua si la tabla no existe
                    cursor.execute("""
                        SELECT id, categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion
                        FROM ejercicios 
                        WHERE nivel = %s AND activo = TRUE
                        ORDER BY RANDOM() 
                        LIMIT 1
                    """, (user_level,))

                result = cursor.fetchone()
                if result:
                    from src.models.exercise import Exercise
                    return Exercise(*result)
                return None
        except Exception as e:
            logger.error(f"Error al obtener ejercicio aleatorio: {e}")
            return None