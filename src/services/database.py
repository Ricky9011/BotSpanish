import os
from contextlib import contextmanager
from typing import List, Optional
import psycopg2
from psycopg2 import pool
from src.models.curiosity import Curiosity
from src.models.exercise import Exercise
import logging

class DatabaseService:
    _connection_pool = None

    @classmethod
    def initialize(cls):
        try:
            db_params = {
                "host": os.getenv("DB_HOST"),
                "port": int(os.getenv("DB_PORT") or 5432),
                "dbname": os.getenv("DB_NAME"),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD")
            }
            logging.info(f"Database parameters: {db_params}")
            if None in db_params.values():
                raise ValueError(f"Missing database environment variables: {db_params}")
            cls._connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **db_params
            )
            logging.info("Connection pool initialized successfully")
        except psycopg2.Error as e:
            logging.error(f"Failed to initialize connection pool: {e}")
            raise

    @classmethod
    @contextmanager
    def get_cursor(cls):
        if cls._connection_pool is None:
            raise ValueError("Connection pool not initialized")
        conn = cls._connection_pool.getconn()
        try:
            with conn.cursor() as cursor:
                yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
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

    @classmethod
    def clear_exercises(cls):
            """Elimina todos los ejercicios de la base de datos"""
            with cls.get_cursor() as cursor:
                cursor.execute("DELETE FROM ejercicios")

    @classmethod
    def clear_curiosities(cls):
            """Elimina todas las curiosidades de la base de datos"""
            with cls.get_cursor() as cursor:
                cursor.execute("DELETE FROM curiosidades")