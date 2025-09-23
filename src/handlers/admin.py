import os
import json
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from src.services.database import DatabaseService
from src.utils.exercise_utils import validate_exercises_json, load_exercises_from_json

# Configuración del logger para registrar mensajes de depuración e información
logger = logging.getLogger(__name__)

# Creación de un router para manejar comandos específicos
router = Router(name="admin")

def is_admin(user_id: int) -> bool:
    """
    Verifica si un usuario tiene permisos de administrador.

    Args:
        user_id (int): ID del usuario a verificar.

    Returns:
        bool: True si el usuario es administrador, False en caso contrario.
    """
    return user_id == int(os.getenv("ADMIN_USER_ID"))

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """
    Muestra el panel de administración si el usuario tiene permisos de administrador.

    Args:
        message (Message): Mensaje recibido del usuario.

    Responde con un mensaje que contiene los comandos disponibles para administradores.
    """
    try:
        if not is_admin(message.from_user.id):
            await message.answer("❌ No tienes permisos de administrador.")
            return
    except ValueError:
        await message.answer("❌ Error de configuración del administrador.")
        return

    await message.answer(
        "🛠️ **Panel de Administración**\n\n"
        "Comandos disponibles:\n"
        "/stats - Estadísticas del bot\n"
        "/users - Lista de usuarios\n"
        "/broadcast - Enviar mensaje a todos los usuarios"
    )

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """
    Muestra estadísticas del bot, como el número total de usuarios y ejercicios completados.

    Args:
        message (Message): Mensaje recibido del usuario.

    Recupera datos de la base de datos y responde con un resumen de estadísticas.
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ No tienes permisos de administrador.")
        return

    with DatabaseService.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(exercises) FROM users")
        total_exercises = cursor.fetchone()[0] or 0

        cursor.execute("SELECT level, COUNT(*) FROM users GROUP BY level")
        levels = cursor.fetchall()

    stats_text = (
        f"📊 **Estadísticas del Bot**\n\n"
        f"👥 Usuarios totales: {total_users}\n"
        f"✅ Ejercicios completados: {total_exercises}\n\n"
        f"📈 Distribución por nivel:\n"
    )
    stats_text += "\n".join(f"- {level.capitalize()}: {count} usuarios" for level, count in levels)
    await message.answer(stats_text)

@router.message(Command("load_exercises"))
async def cmd_load_exercises(message: Message):
    """
    Carga ejercicios desde un archivo JSON y los inserta en la base de datos.

    Args:
        message (Message): Mensaje recibido del usuario.

    - Valida el archivo JSON antes de cargar los datos.
    - Inserta los ejercicios en la base de datos, eliminando los existentes previamente.
    - Responde con un mensaje indicando el resultado de la operación.
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ No tienes permisos de administrador.")
        return

    try:
        json_path = "ejercicios.json"
        errors = validate_exercises_json(json_path)
        if errors:
            error_msg = "❌ Errores en el JSON:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... y {len(errors) - 5} errores más"
            await message.answer(error_msg)
            return

        exercises_data = load_exercises_from_json(json_path)

        with DatabaseService.get_cursor() as cursor:
            cursor.execute("DELETE FROM ejercicios")
            cursor.execute("ALTER SEQUENCE ejercicios_id_seq RESTART WITH 1")

            inserted_count = 0
            for nivel, categorias in exercises_data.items():
                for categoria, ejercicios in categorias.items():
                    for ejercicio in ejercicios:
                        cursor.execute("""
                            INSERT INTO ejercicios (categoria, nivel, pregunta, opciones, respuesta_correcta, activo)
                            VALUES (%s, %s, %s, %s, %s, TRUE)
                        """, (
                            categoria, nivel, ejercicio["pregunta"],
                            json.dumps(ejercicio["opciones"]),
                            ejercicio["respuesta"]
                        ))
                        inserted_count += 1

        await message.answer(f"✅ Ejercicios cargados exitosamente. Se insertaron {inserted_count} ejercicios.")
    except Exception as e:
        await message.answer(f"❌ Error al cargar ejercicios: {str(e)}")
