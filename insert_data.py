import psycopg2
import json
import os
import re
from dotenv import load_dotenv
import logging

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Establece una conexión a la base de datos PostgreSQL utilizando las variables de entorno.

    Returns:
        psycopg2.extensions.connection: Objeto de conexión a la base de datos.
    """
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def normalize_options(options):
    """
    Normaliza el campo de opciones para asegurar que sea una lista válida para el tipo TEXT[].

    Args:
        options (str | list): Opciones en formato de lista o cadena.

    Returns:
        list: Lista de opciones normalizadas.

    Raises:
        ValueError: Si el formato de las opciones no es soportado.
    """
    if isinstance(options, list):
        # Si ya es una lista, limpiar elementos
        return [str(opt).strip() for opt in options if str(opt).strip()]
    if isinstance(options, str):
        # Manejar formatos como {Perro,Pájaro,Gato,Pez} o ('Perro','Pájaro','Gato','Pez')
        cleaned = options.strip('{}()').replace('"', '').replace("'", "")
        # Dividir por comas, asegurando que no se rompa por comas dentro de comillas
        items = [item.strip() for item in re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', cleaned) if item.strip()]
        return items
    raise ValueError(f"Formato de opciones no soportado: {options}")

def fix_existing_exercises():
    """
    Corrige las opciones existentes en la base de datos para asegurar que estén normalizadas.

    - Recupera los ejercicios de la base de datos.
    - Normaliza las opciones y verifica que la respuesta correcta esté dentro del rango.
    - Actualiza los ejercicios en la base de datos si es necesario.

    Logs:
        Registra los ejercicios corregidos, errores encontrados y el total de ejercicios.

    Raises:
        Exception: Si ocurre un error durante la corrección.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, opciones, respuesta_correcta FROM ejercicios")
        ejercicios = cursor.fetchall()
        fixed_count = 0
        for ejercicio_id, opciones, respuesta in ejercicios:
            try:
                # Normalizar opciones
                normalized = normalize_options(opciones)
                # Verificar si la respuesta está en rango
                if not (0 <= respuesta < len(normalized)):
                    raise ValueError(
                        f"Respuesta fuera de rango para ID {ejercicio_id}: {respuesta} con {len(normalized)} opciones")
                # Solo actualizar si las opciones han cambiado
                if normalized != opciones:
                    cursor.execute(
                        "UPDATE ejercicios SET opciones = %s WHERE id = %s",
                        (normalized, ejercicio_id)
                    )
                    fixed_count += 1
                    logger.info(f"Ejercicio {ejercicio_id} corregido: {normalized}")
                else:
                    logger.info(f"Ejercicio {ejercicio_id} ya está normalizado")
            except Exception as e:
                logger.error(f"Error corrigiendo ejercicio {ejercicio_id}: {e}")
        conn.commit()
        logger.info(f"Corrección completada. Ejercicios corregidos: {fixed_count}")
        # Verificar el total de ejercicios
        cursor.execute("SELECT COUNT(*) FROM ejercicios")
        total = cursor.fetchone()[0]
        logger.info(f"Total ejercicios en la base de datos: {total}")
    except Exception as e:
        logger.error(f"Error durante la corrección: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def import_from_json(json_path):
    """
    Importa ejercicios desde un archivo JSON y los inserta en la base de datos.

    Args:
        json_path (str): Ruta al archivo JSON que contiene los ejercicios.

    - Normaliza las opciones y valida los datos antes de insertarlos.
    - Registra los ejercicios insertados y los errores encontrados.

    Logs:
        Registra los ejercicios insertados, errores encontrados y detalles de los fallos.

    Raises:
        Exception: Si ocurre un error durante la importación.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        ejercicios_data = json.load(f)

    inserted_count = 0
    failed = []

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for nivel, categorias in ejercicios_data.items():
            for categoria, ejercicios in categorias.items():
                for ejercicio in ejercicios:
                    try:
                        pregunta = ejercicio.get("pregunta")
                        opciones_raw = ejercicio.get("opciones")
                        respuesta = ejercicio.get("respuesta")
                        explicacion = ejercicio.get("explicacion", "Sin explicación proporcionada")

                        if not isinstance(pregunta, str) or not pregunta:
                            raise ValueError(f"Pregunta inválida en {nivel}/{categoria}")
                        normalized_options = normalize_options(opciones_raw)
                        if not isinstance(respuesta, int) or not (0 <= respuesta < len(normalized_options)):
                            raise ValueError(
                                f"Respuesta inválida en {nivel}/{categoria}: {respuesta} con {len(normalized_options)} opciones")

                        cursor.execute(
                            "INSERT INTO ejercicios (categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion) "
                            "VALUES (%s, %s, %s, %s, %s, %s)",
                            (categoria, nivel, pregunta, normalized_options, respuesta, explicacion)
                        )
                        inserted_count += 1
                        logger.info(f"Insertado ejercicio: {pregunta[:50]}...")
                    except Exception as e:
                        error_msg = f"Error insertando en {nivel}/{categoria}: {str(e)}"
                        logger.error(error_msg)
                        failed.append(error_msg)
        conn.commit()
        logger.info(f"Importación completada. Insertados: {inserted_count}. Fallos: {len(failed)}")
        if failed:
            logger.info("Fallos detallados:")
            for err in failed:
                logger.info(err)
    except Exception as e:
        logger.error(f"Error durante la importación: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Corregir los ejercicios existentes en la base de datos
    fix_existing_exercises()

    # Para importar nuevos ejercicios, descomenta y especifica el path
    import_from_json('data/ejercicios.json')
