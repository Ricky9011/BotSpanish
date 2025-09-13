import os
import psycopg2
from dotenv import load_dotenv


def init_test_db():
    load_dotenv("src/tests/.env.test")

    # Get database connection parameters
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT") or 5432)
    db_name = os.getenv("DB_NAME", "test_db")
    db_user = os.getenv("DB_USER", "test_user")
    db_password = os.getenv("DB_PASSWORD", "test_password")

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )

        with conn.cursor() as cursor:
            # Drop existing tables to ensure clean state
            cursor.execute("DROP TABLE IF EXISTS feedback, users, ejercicios, curiosidades CASCADE;")

            # Create tables
            cursor.execute("""
                CREATE TABLE users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    level VARCHAR(50) DEFAULT 'principiante',
                    exercises INTEGER DEFAULT 0,
                    referrals INTEGER DEFAULT 0,
                    challenge_score INTEGER DEFAULT 0,
                    streak_days INTEGER DEFAULT 0,
                    completed_exercises TEXT DEFAULT '',
                    last_practice TIMESTAMP
                );

                CREATE TABLE ejercicios (
                    id SERIAL PRIMARY KEY,
                    categoria VARCHAR(255) NOT NULL,
                    nivel VARCHAR(50) NOT NULL,
                    pregunta TEXT NOT NULL,
                    opciones TEXT NOT NULL,
                    respuesta_correcta INTEGER NOT NULL,
                    explicacion TEXT,
                    activo BOOLEAN DEFAULT TRUE
                );

                CREATE TABLE curiosidades (
                    id SERIAL PRIMARY KEY,
                    categoria VARCHAR(255) NOT NULL,
                    texto TEXT NOT NULL,
                    activo BOOLEAN DEFAULT TRUE
                );

                CREATE TABLE feedback (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Insert test data
            cursor.execute("""
                INSERT INTO users (user_id, username, level, exercises) 
                VALUES (2006572428, 'test_user', 'principiante', 5);

                INSERT INTO ejercicios (categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion)
                VALUES 
                ('gramática', 'principiante', '¿Cuál es el artículo masculino singular?', 
                 '["el", "la", "los", "las"]', 0, 'El artículo masculino singular es "el".'),

                ('vocabulario', 'principiante', '¿Cómo se dice "house" en español?', 
                 '["casa", "perro", "gato", "libro"]', 0, 'House se dice "casa" en español.');

                INSERT INTO curiosidades (categoria, texto)
                VALUES 
                ('gramática', 'En español, los adjetivos generalmente van después del sustantivo.'),
                ('cultura', 'El español es el segundo idioma más hablado del mundo como lengua nativa.');
            """)

            conn.commit()
        conn.close()
        print("Test database initialized successfully")

    except Exception as e:
        print(f"Error initializing test database: {e}")
        raise


if __name__ == "__main__":
    init_test_db()