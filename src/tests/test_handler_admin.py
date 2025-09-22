import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import Message

from src.handlers.admin import cmd_load_exercises, cmd_stats, cmd_admin


@patch("os.getenv", side_effect=lambda key: "12345" if key == "ADMIN_USER_ID" else None)
async def test_cmd_admin_with_admin_user(mock_getenv):
    message = AsyncMock(spec=Message)
    message.from_user.id = 12345

    await cmd_admin(message)

    message.answer.assert_called_once_with(
        "🛠️ **Panel de Administración**\n\n"
        "Comandos disponibles:\n"
        "/stats - Estadísticas del bot\n"
        "/users - Lista de usuarios\n"
        "/broadcast - Enviar mensaje a todos los usuarios"
    )

@patch("os.getenv", side_effect=lambda key: "12345" if key == "ADMIN_USER_ID" else None)
async def test_cmd_admin_with_non_admin_user(mock_getenv):
    message = AsyncMock(spec=Message)
    message.from_user.id = 67890

    await cmd_admin(message)

    message.answer.assert_called_once_with("❌ No tienes permisos de administrador.")

@patch("os.getenv", side_effect=lambda key: None)
async def test_cmd_admin_with_invalid_admin_config(mock_getenv):
    message = AsyncMock(spec=Message)
    message.from_user.id = 12345

    await cmd_admin(message)

    message.answer.assert_called_once_with("❌ Error de configuración del administrador.")

@patch("src.services.database.DatabaseService.get_cursor")
@patch("os.getenv", side_effect=lambda key: "12345" if key == "ADMIN_USER_ID" else None)
async def test_cmd_stats_with_admin_user(mock_getenv, mock_get_cursor):
    message = AsyncMock(spec=Message)
    message.from_user.id = 12345

    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = [(10,), (50,)]
    mock_cursor.fetchall.return_value = [("beginner", 5), ("advanced", 5)]
    mock_get_cursor.return_value = mock_cursor

    await cmd_stats(message)

    message.answer.assert_called_once_with(
        "📊 **Estadísticas del Bot**\n\n"
        "👥 Usuarios totales: 10\n"
        "✅ Ejercicios completados: 50\n\n"
        "📈 Distribución por nivel:\n"
        "- Beginner: 5 usuarios\n"
        "- Advanced: 5 usuarios"
    )

@patch("src.services.database.DatabaseService.get_cursor")
@patch("os.getenv", side_effect=lambda key: "12345" if key == "ADMIN_USER_ID" else None)
async def test_cmd_stats_with_non_admin_user(mock_getenv, mock_get_cursor):
    message = AsyncMock(spec=Message)
    message.from_user.id = 67890

    await cmd_stats(message)

    message.answer.assert_called_once_with("❌ No tienes permisos de administrador.")

@patch("src.utils.exercise_utils.validate_exercises_json", return_value=[])
@patch("src.utils.exercise_utils.load_exercises_from_json")
@patch("src.services.database.DatabaseService.get_cursor")
@patch("os.getenv", side_effect=lambda key: "12345" if key == "ADMIN_USER_ID" else None)
async def test_cmd_load_exercises_success(mock_getenv, mock_get_cursor, mock_load_exercises, mock_validate_json):
    message = AsyncMock(spec=Message)
    message.from_user.id = 12345

    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_get_cursor.return_value = mock_cursor

    mock_load_exercises.return_value = {
        "beginner": {
            "math": [
                {"pregunta": "2+2?", "opciones": ["3", "4"], "respuesta": 1}
            ]
        }
    }

    await cmd_load_exercises(message)

    mock_cursor.execute.assert_any_call("DELETE FROM ejercicios")
    mock_cursor.execute.assert_any_call("ALTER SEQUENCE ejercicios_id_seq RESTART WITH 1")
    mock_cursor.execute.assert_any_call(
        """
        INSERT INTO ejercicios (categoria, nivel, pregunta, opciones, respuesta_correcta, activo)
        VALUES (%s, %s, %s, %s, %s, TRUE)
        """,
        ("math", "beginner", "2+2?", '["3", "4"]', 1)
    )
    message.answer.assert_called_once_with("✅ Ejercicios cargados exitosamente. Se insertaron 1 ejercicios.")

@patch("src.utils.exercise_utils.validate_exercises_json", return_value=["Error 1", "Error 2"])
@patch("os.getenv", side_effect=lambda key: "12345" if key == "ADMIN_USER_ID" else None)
async def test_cmd_load_exercises_with_json_errors(mock_getenv, mock_validate_json):
    message = AsyncMock(spec=Message)
    message.from_user.id = 12345

    await cmd_load_exercises(message)

    message.answer.assert_called_once_with("❌ Errores en el JSON:\nError 1\nError 2")
