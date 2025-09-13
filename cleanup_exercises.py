# cleanup_exercises.py
import json
from pathlib import Path
from src.services.database import DatabaseService


def cleanup_and_load_exercises():
    # Limpiar la tabla de ejercicios
    with DatabaseService.get_cursor() as cursor:
        cursor.execute("DELETE FROM ejercicios")
        cursor.execute("ALTER SEQUENCE ejercicios_id_seq RESTART WITH 1")
        print("Tabla de ejercicios limpiada.")

    # Cargar ejercicios desde JSON
    json_path = Path("ejercicios.json")

    if not json_path.exists():
        print("❌ No se encontró el archivo ejercicios.json")
        return

    with open(json_path, 'r', encoding='utf-8') as file:
        exercises_data = json.load(file)

    # Insertar ejercicios normalizados
    inserted_count = 0
    with DatabaseService.get_cursor() as cursor:
        for nivel, categorias in exercises_data.items():
            for categoria, ejercicios in categorias.items():
                for ejercicio in ejercicios:
                    # Normalizar y validar el ejercicio
                    opciones = ejercicio["opciones"]
                    respuesta_correcta = ejercicio["respuesta"]

                    # Validar que la respuesta esté dentro del rango de opciones
                    if respuesta_correcta < 0 or respuesta_correcta >= len(opciones):
                        print(f"⚠️ Respuesta inválida en ejercicio: {ejercicio['pregunta'][:50]}...")
                        continue

                    # Convertir opciones a formato JSON string
                    opciones_json = json.dumps(opciones)

                    # Insertar en la base de datos
                    cursor.execute("""
                        INSERT INTO ejercicios (categoria, nivel, pregunta, opciones, respuesta_correcta, activo)
                        VALUES (%s, %s, %s, %s, %s, TRUE)
                    """, (categoria, nivel, ejercicio["pregunta"], opciones_json, respuesta_correcta))

                    inserted_count += 1

    print(f"✅ {inserted_count} ejercicios cargados exitosamente.")


if __name__ == "__main__":
    cleanup_and_load_exercises()