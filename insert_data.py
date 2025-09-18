import json
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar bot y dispatcher
bot = Bot(token=os.getenv("BOT_TOKEN"))  # Use token from environment
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)


# Definir estados para el proceso de importación
class ImportStates(StatesGroup):
    WAITING_FOR_JSON = State()


# Lista de IDs de administradores (carga desde .env)
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]


# Función para obtener conexión a la base de datos
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )


# Función para normalizar opciones
def normalize_options(options):
    """Normaliza el campo opciones para asegurar que sea una lista válida."""
    if isinstance(options, list):
        return options
    elif isinstance(options, str):
        try:
            # Intentar parsear como JSON
            parsed = json.loads(options)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return list(parsed.values())
            else:
                raise ValueError(f"Formato de opciones no válido: {options}")
        except json.JSONDecodeError:
            # Manejar casos como {op1,op2,op3}
            cleaned = options.strip('{}').replace('"', '').split(',')
            return [opt.strip() for opt in cleaned if opt.strip()]
    else:
        raise ValueError(f"Formato de opciones no soportado: {options}")


# Función para normalizar un ejercicio
def normalize_exercise(ejercicio, nivel, categoria):
    """Valida y normaliza un ejercicio."""
    if not isinstance(ejercicio.get("pregunta"), str) or not ejercicio["pregunta"]:
        raise ValueError(f"Pregunta inválida en {nivel}/{categoria}: {ejercicio}")
    if not isinstance(ejercicio.get("opciones"), (list, str)) or not ejercicio["opciones"]:
        raise ValueError(f"Opciones inválidas en {nivel}/{categoria}: {ejercicio['opciones']}")
    if not isinstance(ejercicio.get("respuesta"), int):
        raise ValueError(f"Respuesta inválida en {nivel}/{categoria}: {ejercicio['respuesta']}")

    # Normalizar opciones
    normalized_options = normalize_options(ejercicio["opciones"])
    if not (0 <= ejercicio["respuesta"] < len(normalized_options)):
        raise ValueError(f"Respuesta fuera de rango en {nivel}/{categoria}: {ejercicio['respuesta']}")

    return {
        "pregunta": ejercicio["pregunta"],
        "opciones": normalized_options,  # Lista para columna TEXT[]
        "respuesta": ejercicio["respuesta"],
        "explicacion": ejercicio.get("explicacion", "Sin explicación proporcionada")
    }


# Función para importar JSON a la base de datos
async def import_json_to_db(file_content, chat_id, bot):
    """Importa un archivo JSON a la base de datos, normalizando los datos."""
    try:
        # Parsear el contenido del archivo
        ejercicios_data = json.loads(file_content)
        inserted_exercises = 0
        failed_exercises = []

        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Procesar cada ejercicio
        for nivel, categorias in ejercicios_data.items():
            for categoria, ejercicios in categorias.items():
                for ejercicio in ejercicios:
                    try:
                        normalized_exercise = normalize_exercise(ejercicio, nivel, categoria)

                        # Insertar en la base de datos
                        cursor.execute(
                            "INSERT INTO ejercicios (categoria, nivel, pregunta, opciones, respuesta_correcta, explicacion) VALUES (%s, %s, %s, %s, %s, %s)",
                            (
                                categoria,
                                nivel,
                                normalized_exercise["pregunta"],
                                normalized_exercise["opciones"],
                                normalized_exercise["respuesta"],
                                normalized_exercise["explicacion"]
                            )
                        )
                        inserted_exercises += 1
                        logger.info(f"Insertado ejercicio: {normalized_exercise['pregunta'][:50]}...")
                    except Exception as e:
                        error_msg = f"Error insertando ejercicio en {nivel}/{categoria}: {str(e)}"
                        logger.error(error_msg)
                        failed_exercises.append(error_msg)

        # Confirmar los cambios
        conn.commit()

        # Obtener el conteo total de ejercicios
        cursor.execute("SELECT COUNT(*) FROM ejercicios")
        total_ejercicios = cursor.fetchone()[0]

        # Cerrar conexión
        cursor.close()
        conn.close()

        # Preparar mensaje de resultado
        message = f"¡Importación completa! Ejercicios insertados: {inserted_exercises}\nTotal ejercicios en DB: {total_ejercicios}"

        # Agregar información sobre errores si los hubo
        if failed_exercises:
            message += f"\n\nErrores encontrados ({len(failed_exercises)}):"
            for i, error in enumerate(failed_exercises[:5]):  # Mostrar solo los primeros 5 errores
                message += f"\n{i + 1}. {error}"
            if len(failed_exercises) > 5:
                message += f"\n... y {len(failed_exercises) - 5} errores más."

        await bot.send_message(chat_id, message)

    except json.JSONDecodeError:
        await bot.send_message(chat_id, "Error: El archivo JSON tiene un formato inválido.")
    except Exception as e:
        await bot.send_message(chat_id, f"Error procesando el archivo: {str(e)}")


# Comando para iniciar la importación
@dp.message(Command("import_json"))
async def cmd_import_json(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("No tienes permiso para usar este comando.")
        return

    # Crear botón inline
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Subir JSON", callback_data="upload_json")]
    ])
    await message.answer(
        "Haz clic en el botón para subir un archivo JSON con ejercicios.",
        reply_markup=keyboard
    )
    await state.set_state(ImportStates.WAITING_FOR_JSON)


# Manejador para el botón
@dp.callback_query(lambda c: c.data == "upload_json")
async def process_upload_button(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Por favor, sube el archivo JSON.")
    await callback_query.answer()


# Manejador para el archivo JSON
@dp.message(ImportStates.WAITING_FOR_JSON)
async def process_json_file(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("No tienes permiso para usar este comando.")
        return

    if not message.document or not message.document.file_name.endswith(".json"):
        await message.answer("Por favor, sube un archivo JSON válido.")
        return

    try:
        # Descargar el archivo
        file = await bot.get_file(message.document.file_id)
        file_content = await bot.download_file(file.file_path)
        file_content = file_content.read().decode("utf-8")

        # Importar el archivo
        await import_json_to_db(file_content, message.chat.id, bot)

        # Limpiar estado
        await state.clear()
    except Exception as e:
        await message.answer(f"Error al procesar el archivo: {str(e)}")
        await state.clear()


# Iniciar el bot
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())