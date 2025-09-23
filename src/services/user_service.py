# services/user_service.py
from src.services.database import DatabaseService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def register_user(user_id: int, username: str):
        """Registra un nuevo usuario - VERSIÓN CORREGIDA"""
        with DatabaseService.get_cursor() as cursor:
            # Verificar si el usuario ya existe
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            existing_user = cursor.fetchone()

            if existing_user:
                logger.info(f"Usuario {user_id} ya existe, omitiendo registro")
                return

            # Insertar usuario con columnas que SÍ existen
            cursor.execute("""
                INSERT INTO users (user_id, username, level, exercises, referrals, challenge_score, streak_days, last_practice)
                VALUES (%s, %s, 'principiante', 0, 0, 0, 0, NULL)
            """, (user_id, username))
            logger.info(f"Nuevo usuario registrado: {user_id}")

    @staticmethod
    def get_user_stats(user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas del usuario desde la tabla user_ejercicios"""
        with DatabaseService.get_cursor() as cursor:
            # Obtener nivel del usuario
            cursor.execute("SELECT level FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            if not result:
                return None

            level = result[0]

            # Contar ejercicios completados desde user_ejercicios
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_ejercicios 
                WHERE user_id = %s AND is_correct = true
            """, (user_id,))
            exercises_completed = cursor.fetchone()[0]

            # Obtener última práctica
            cursor.execute("""
                SELECT MAX(completed_at) 
                FROM user_ejercicios 
                WHERE user_id = %s
            """, (user_id,))
            last_practice_result = cursor.fetchone()
            last_practice = last_practice_result[0] if last_practice_result[0] else None

            # Obtener estadísticas por nivel
            cursor.execute("""
                SELECT nivel, COUNT(*) 
                FROM user_ejercicios 
                WHERE user_id = %s AND is_correct = true
                GROUP BY nivel
            """, (user_id,))
            exercises_by_level = {row[0]: row[1] for row in cursor.fetchall()}

            # Obtener estadísticas por categoría
            cursor.execute("""
                SELECT categoria, COUNT(*) 
                FROM user_ejercicios 
                WHERE user_id = %s AND is_correct = true
                GROUP BY categoria
            """, (user_id,))
            exercises_by_category = {row[0]: row[1] for row in cursor.fetchall()}

            # Calcular racha (días consecutivos con al menos un ejercicio correcto)
            cursor.execute("""
                SELECT COUNT(DISTINCT DATE(completed_at))
                FROM user_ejercicios 
                WHERE user_id = %s 
                AND is_correct = true
                AND completed_at >= CURRENT_DATE - INTERVAL '7 days'
            """, (user_id,))
            streak_days = cursor.fetchone()[0]

            return {
                "level": level,
                "exercises": exercises_completed,
                "streak_days": streak_days,
                "referrals": 0,  # Placeholder
                "challenge_score": 0,  # Placeholder
                "last_practice": last_practice,
                "exercises_by_level": exercises_by_level,
                "exercises_by_category": exercises_by_category
            }

    @staticmethod
    def set_user_level(user_id: int, level: str):
        """Actualiza el nivel del usuario"""
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                UPDATE users 
                SET level = %s 
                WHERE user_id = %s
            """, (level, user_id))

    @staticmethod
    def get_user_level(user_id: int) -> str:
        """Obtiene el nivel del usuario"""
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("SELECT level FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else "principiante"