import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.services.database import DatabaseService
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar bot y dispatcher
bot = Bot(token="YOUR_BOT_TOKEN")  # Reemplaza con tu token
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)


# Definir estados para el proceso de importación
class ImportStates(StatesGroup):
    WAITING_FOR_JSON = State()


# Lista de IDs de administradores (carga desde .env o una DB en producción)
ADMIN_IDS = [123456789]  # Reemplaza con los IDs reales


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

    # Serializar opciones como JSON para la columna TEXT
    options_json = json.dumps(normalized_options, ensure_ascii=False)

    return {
        "pregunta": ejercicio["pregunta"],
        "opciones": options_json,  # Cadena JSON para columna TEXT
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

        # Normalizar e importar
        for nivel, categorias in ejercicios_data.items():
            for categoria, ejercicios in categorias.items():
                for ejercicio in ejercicios:
                    try:
                        normalized_exercise = normalize_exercise(ejercicio, nivel, categoria)
                        DatabaseService.add_exercise(
                            categoria=categoria,
                            nivel=nivel,
                            pregunta=normalized_exercise["pregunta"],
                            opciones=normalized_exercise["opciones"],  # Ya es una cadena JSON
                            respuesta_correcta=normalized_exercise["respuesta"],
                            explicacion=normalized_exercise["explicacion"]
                        )
                        inserted_exercises += 1
                        logger.info(f"Insertado ejercicio: {normalized_exercise['pregunta'][:50]}...")
                    except Exception as e:
                        logger.error(f"Error insertando ejercicio en {nivel}/{categoria}: {e}")
                        await bot.send_message(chat_id, f"Error insertando ejercicio: {str(e)}")

        # Verificar conteos
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ejercicios")
            total_ejercicios = cursor.fetchone()[0]

        await bot.send_message(
            chat_id,
            f"¡Importación completa! Ejercicios insertados: {inserted_exercises}\n"
            f"Total ejercicios en DB: {total_ejercicios}"
        )
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
    DatabaseService.initialize()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())