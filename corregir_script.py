import psycopg2
import json
import re
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()


def get_db_connection():
    """Obtener conexión directa a la base de datos"""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )


def normalize_options(options):
    """Normaliza el campo opciones para convertirlo en una lista válida."""
    if isinstance(options, list):
        return options

    # Si ya es un string JSON válido, parsearlo
    if isinstance(options, str):
        # Intentar parsear como JSON primero
        try:
            parsed = json.loads(options)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return list(parsed.values())
        except json.JSONDecodeError:
            pass

        # Manejar el formato con {op1,op2,op3}
        if options.startswith('{') and options.endswith('}'):
            # Eliminar las llaves y dividir por comas
            cleaned = options[1:-1].split(',')
            # Limpiar cada opción y eliminar espacios
            return [opt.strip().replace('"', '') for opt in cleaned if opt.strip()]

        # Si es un string simple, tratar de dividirlo por comas
        if ',' in options:
            return [opt.strip() for opt in options.split(',') if opt.strip()]

        # Si no hay comas, devolver como lista de un elemento
        return [options.strip()]

    # Si es otro tipo, convertirlo a string y luego a lista
    return [str(options)]


def fix_exercise_options():
    """Corregir las opciones de los ejercicios en la base de datos"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Obtener solo los ejercicios problemáticos (ID 60-120)
        cursor.execute("SELECT id, opciones FROM ejercicios" )
        ejercicios = cursor.fetchall()

        updated_count = 0
        for ejercicio_id, opciones in ejercicios:
            try:
                # Normalizar las opciones
                opciones_normalizadas = normalize_options(opciones)

                # Convertir a JSON string
                opciones_json = json.dumps(opciones_normalizadas, ensure_ascii=False)

                # Actualizar la base de datos con las opciones corregidas
                cursor.execute(
                    "UPDATE ejercicios SET opciones = %s WHERE id = %s",
                    (opciones_json, ejercicio_id)
                )
                print(f"Ejercicio {ejercicio_id} corregido: {opciones} -> {opciones_json}")
                updated_count += 1

            except Exception as e:
                print(f"Error procesando ejercicio {ejercicio_id}: {e}")

        # Confirmar los cambios
        conn.commit()
        print(f"Corrección completada. {updated_count} ejercicios actualizados.")

    except Exception as e:
        print(f"Error durante la corrección: {e}")
        conn.rollback()

    finally:
        # Cerrar la conexión
        cursor.close()
        conn.close()


if __name__ == "__main__":
    fix_exercise_options()