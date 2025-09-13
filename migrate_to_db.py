import json
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def migrate_data():
    # Conexión a la base de datos
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()

    # Crear tablas si no existen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ejercicios (
            id SERIAL PRIMARY KEY,
            categoria VARCHAR(100) NOT NULL,
            nivel VARCHAR(20) NOT NULL,
            pregunta TEXT NOT NULL,
            opciones TEXT[] NOT NULL,
            respuesta_correcta INTEGER NOT NULL,
            explicacion TEXT,
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS curiosidades (
            id SERIAL PRIMARY KEY,
            categoria VARCHAR(100) NOT NULL,
            texto TEXT NOT NULL,
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migrar ejercicios
    with open('data/ejercicios.json', 'r', encoding='utf-8') as f:
        ejercicios_data = json.load(f)

        for nivel, categorias in ejercicios_data.items():
            for categoria, ejercicios in categorias.items():
                for ejercicio in ejercicios:
                    cursor.execute(
                        "INSERT INTO ejercicios (categoria, nivel, pregunta, opciones, respuesta_correcta) VALUES (%s, %s, %s, %s, %s)",
                        (categoria, nivel, ejercicio['pregunta'], ejercicio['opciones'], ejercicio['respuesta'])
                    )

    # Migrar curiosidades
    with open('data/curiosidades.json', 'r', encoding='utf-8') as f:
        curiosidades_data = json.load(f)

        for curiosidad in curiosidades_data['curiosidades']:
            cursor.execute(
                "INSERT INTO curiosidades (categoria, texto) VALUES (%s, %s)",
                (curiosidad['categoria'], curiosidad['texto'])
            )

    conn.commit()
    cursor.close()
    conn.close()
    print("Migración completada exitosamente!")


if __name__ == "__main__":
    migrate_data()