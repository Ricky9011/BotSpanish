
from src.models.curiosity import Curiosity
from src.services.database import DatabaseService


class CuriosityService:
    @staticmethod
    def get_random_curiosity() -> Curiosity:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, categoria, texto 
                FROM curiosidades 
                WHERE activo = TRUE 
                ORDER BY RANDOM() 
                LIMIT 1
            """)

            result = cursor.fetchone()
            if result:
                return Curiosity(*result)
            return None

    @staticmethod
    def add_curiosity(categoria: str, texto: str) -> int:
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO curiosidades (categoria, texto)
                VALUES (%s, %s)
                RETURNING id
            """, (categoria, texto))

            return cursor.fetchone()[0]