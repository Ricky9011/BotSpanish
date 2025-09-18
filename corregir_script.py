# correction_script.py
import json
from src.services.database import DatabaseService


def fix_exercise_options():
    with DatabaseService.get_cursor() as cursor:
        # Obtener todos los ejercicios
        cursor.execute("SELECT id, opciones FROM ejercicios")
        exercises = cursor.fetchall()

        for exercise_id, opciones in exercises:
            if isinstance(opciones, str) and not opciones.startswith('['):
                # Convertir a formato JSON
                try:
                    # Si ya es JSON, saltar
                    json.loads(opciones)
                except (json.JSONDecodeError, TypeError):
                    # Si no es JSON, convertir a array JSON
                    # Asumiendo que las opciones están separadas por comas
                    options_list = [opt.strip() for opt in opciones.split(',')]
                    options_json = json.dumps(options_list)

                    # Actualizar la base de datos
                    cursor.execute("""
                        UPDATE ejercicios 
                        SET opciones = %s 
                        WHERE id = %s
                    """, (options_json, exercise_id))

        print("Corrección de opciones completada")


if __name__ == "__main__":
    fix_exercise_options()