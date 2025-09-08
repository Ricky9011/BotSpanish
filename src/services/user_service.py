from src.services.database_service import DatabaseService


class UserService:
    @staticmethod
    def get_user_level(user_id: int) -> str:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("SELECT level FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else "principiante"

    @staticmethod
    def get_completed_exercises(user_id: int) -> List[int]:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("SELECT completed_exercises FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()

            if result and result[0]:
                return [int(id_str) for id_str in result[0].split(",") if id_str.strip()]
            return []

    @staticmethod
    def add_completed_exercise(user_id: int, exercise_id: int):
        completed_exercises = UserService.get_completed_exercises(user_id)

        if exercise_id not in completed_exercises:
            completed_exercises.append(exercise_id)
            completed_str = ",".join(str(id) for id in completed_exercises)

            with DatabaseService.get_cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET completed_exercises = %s WHERE user_id = %s",
                    (completed_str, user_id)
                )

    @staticmethod
    def reset_completed_exercises(user_id: int):
        with DatabaseService.get_cursor() as cursor:
            cursor.execute(
                "UPDATE users SET completed_exercises = '' WHERE user_id = %s",
                (user_id,)
            )