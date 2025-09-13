import os
import json
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from src.services.database import DatabaseService

from src.utils.exercise_utils import validate_exercises_json, load_exercises_from_json

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == int(os.getenv("ADMIN_USER_ID"))


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    # Verificar si el usuario es administrador
    try:
        admin_id = int(os.getenv("ADMIN_USER_ID"))
        if message.from_user.id != admin_id:
            await message.answer("❌ No tienes permisos de administrador.")
            return
    except (ValueError, TypeError):
        await message.answer("❌ Error de configuración del administrador.")
        return

    admin_text = (
        "🛠️ **Panel de Administración**\n\n"
        "Comandos disponibles:\n"
        "/stats - Estadísticas del bot\n"
        "/users - Lista de usuarios\n"
        "/broadcast - Enviar mensaje a todos los usuarios"
    )

    await message.answer(admin_text)


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    with DatabaseService.get_cursor() as cursor:
        # Estadísticas de usuarios
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

        for level, count in levels:
            stats_text += f"- {level.capitalize()}: {count} usuarios\n"

        await message.answer(stats_text)


@router.message(Command("load_exercises"))
async def cmd_load_exercises(message: Message):
    # Verificar si el usuario es administrador
    if message.from_user.id != int(os.getenv("ADMIN_USER_ID")):
        await message.answer("❌ No tienes permisos de administrador.")
        return

    try:
        # Ruta al archivo JSON
        json_path = "ejercicios.json"

        # Validar primero
        errors = validate_exercises_json(json_path)
        if errors:
            error_msg = "❌ Errores en el JSON:\n" + "\n".join(errors[:5])  # Mostrar solo los primeros 5 errores
            if len(errors) > 5:
                error_msg += f"\n... y {len(errors) - 5} errores más"
            await message.answer(error_msg)
            return

        # Cargar datos validados
        exercises_data = load_exercises_from_json(json_path)

        # Limpiar la tabla de ejercicios
        with DatabaseService.get_cursor() as cursor:
            cursor.execute("DELETE FROM ejercicios")
            cursor.execute("ALTER SEQUENCE ejercicios_id_seq RESTART WITH 1")

        # Insertar ejercicios normalizados
        inserted_count = 0
        with DatabaseService.get_cursor() as cursor:
            for nivel, categorias in exercises_data.items():
                for categoria, ejercicios in categorias.items():
                    for ejercicio in ejercicios:
                        opciones = ejercicio["opciones"]
                        respuesta_correcta = ejercicio["respuesta"]

                        # Convertir opciones a formato JSON string
                        opciones_json = json.dumps(opciones)

                        # Insertar en la base de datos
                        cursor.execute("""
                            INSERT INTO ejercicios (categoria, nivel, pregunta, opciones, respuesta_correcta, activo)
                            VALUES (%s, %s, %s, %s, %s, TRUE)
                        """, (categoria, nivel, ejercicio["pregunta"], opciones_json, respuesta_correcta))

                        inserted_count += 1

        await message.answer(f"✅ Ejercicios cargados exitosamente. Se insertaron {inserted_count} ejercicios.")

    except Exception as e:
        await message.answer(f"❌ Error al cargar ejercicios: {str(e)}")