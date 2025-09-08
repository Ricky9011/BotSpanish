import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import os
from typing import List, Optional
from src.models.exercise import Exercise
from src.models.curiosity import Curiosity


class DatabaseService:
    _connection_pool = None

    @classmethod
    def initialize(cls):
        cls._connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

    @classmethod
    @contextmanager
    def get_cursor(cls):
        conn = cls._connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cls._connection_pool.putconn(conn)

    @classmethod
    def get_random_exercise(cls, nivel: str, excluded_ids: List[int] = None) -> Optional[Exercise]:
        if excluded_ids is None:
            excluded_ids = []

        with cls.get_cursor() as cursor:
            query = """
                SELECT id, categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion
                FROM ejercicios 
                WHERE nivel = %s AND activo = TRUE
            """
            params = [nivel]

            if excluded_ids:
                query += " AND id NOT IN %s"
                params.append(tuple(excluded_ids))

            query += " ORDER BY RANDOM() LIMIT 1"

            cursor.execute(query, params)
            result = cursor.fetchone()

            if result:
                return Exercise(*result)
            return None

    @classmethod
    def get_random_curiosity(cls) -> Optional[Curiosity]:
        with cls.get_cursor() as cursor:
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

    @classmethod
    def add_exercise(cls, categoria: str, nivel: str, pregunta: str,
                     opciones: List[str], respuesta_correcta: int, explicacion: str = None) -> int:
        with cls.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO ejercicios (categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion))

            return cursor.fetchone()[0]

    @classmethod
    def add_curiosity(cls, categoria: str, texto: str) -> int:
        with cls.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO curiosidades (categoria, texto)
                VALUES (%s, %s)
                RETURNING id
            """, (categoria, texto))

            return cursor.fetchone()[0]


# Inicializar el pool de conexiones al importar
DatabaseService.initialize()
