from src.services.database import DatabaseService
from src.services.exercise_service import ExerciseService


class UserService:
    @classmethod
    def register_user(cls, user_id: int, username: str) -> None:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (user_id, username, level, exercises, referrals, challenge_score, streak_days)
                VALUES (%s, %s, 'principiante', 0, 0, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id, username))

    @classmethod
    def get_user_level(cls, user_id: int) -> str:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("SELECT level FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else "principiante"

    @classmethod
    def update_level(cls, user_id: int, new_level: str) -> None:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("UPDATE users SET level = %s WHERE user_id = %s", (new_level, user_id))

    @classmethod
    def block_user(cls, user_id: int) -> None:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("INSERT INTO blocked_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))

    @classmethod
    def is_blocked(cls, user_id: int) -> bool:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM blocked_users WHERE user_id = %s", (user_id,))
            return cursor.fetchone() is not None

    @classmethod
    def set_reminder(cls, user_id: int, reminder_time: str, timezone: str) -> None:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("INSERT INTO user_reminders (user_id, reminder_time, timezone) VALUES (%s, %s, "
                           "%s) ON CONFLICT (user_id) DO UPDATE SET reminder_time = %s, timezone = %s", (user_id,
                                                                                                         reminder_time,
                                                                                                         timezone,
                                                                                                         reminder_time,
                                                                                                         timezone))

    @classmethod
    def get_achievements(cls, user_id: int) -> list:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                SELECT a.name, a.description, a.icon, ua.earned_at
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_id = a.achievement_id
                WHERE ua.user_id = %s
            """, (user_id,))
            return cursor.fetchall()

    @classmethod
    def get_completed_exercises(cls, user_id: int) -> list[int]:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                SELECT completed_exercises
                FROM users
                WHERE user_id = %s
            """, (user_id,))
            result = cursor.fetchone()
            if result and result[0]:
                return [int(x) for x in result[0].split(",") if x]
            return []

    @classmethod
    def update_user_stats(cls, user_id: int) -> None:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                    UPDATE users
                    SET exercises = exercises + 1,
                        streak_days = CASE
                            WHEN last_practice IS NULL OR last_practice < CURRENT_DATE - INTERVAL '1 day'
                            THEN 1
                            ELSE streak_days + 1
                        END,
                        last_practice = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (user_id,))

    # user_service.py - Modifica el método get_user_stats
    @staticmethod
    def get_user_stats(user_id: int) -> dict:
        """
        Obtiene las estadísticas del usuario
        """
        with DatabaseService.get_cursor() as cursor:
            # Datos básicos del usuario
            cursor.execute("""
                SELECT level, referrals, challenge_score, streak_days, last_practice,
                       (SELECT COUNT(*) FROM user_ejercicios WHERE user_id = %s) as exercises_completed
                FROM users 
                WHERE user_id = %s
            """, (user_id, user_id))

            result = cursor.fetchone()

            if result:
                # Obtener estadísticas por nivel y categoría directamente
                cursor.execute("""
                    SELECT nivel, COUNT(*) 
                    FROM user_ejercicios 
                    WHERE user_id = %s 
                    GROUP BY nivel
                """, (user_id,))
                by_level = {row[0]: row[1] for row in cursor.fetchall()}

                cursor.execute("""
                    SELECT categoria, COUNT(*) 
                    FROM user_ejercicios 
                    WHERE user_id = %s 
                    GROUP BY categoria
                """, (user_id,))
                by_category = {row[0]: row[1] for row in cursor.fetchall()}

                return {
                    'level': result[0],
                    'referrals': result[1],
                    'challenge_score': result[2],
                    'streak_days': result[3],
                    'last_practice': result[4],
                    'exercises': result[5],  # Usamos el contador directo de la consulta
                    'exercises_by_level': by_level,
                    'exercises_by_category': by_category
                }
            else:
                # Si el usuario no existe, crearlo y devolver estadísticas por defecto
                UserService.register_user(user_id, "")
                return {
                    'level': 'principiante',
                    'referrals': 0,
                    'challenge_score': 0,
                    'streak_days': 0,
                    'last_practice': None,
                    'exercises': 0,
                    'exercises_by_level': {},
                    'exercises_by_category': {}
                }
    @classmethod
    def set_user_level(cls, user_id: int, level: str) -> None:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                    UPDATE users
                    SET level = %s
                    WHERE user_id = %s
                """, (level, user_id))
