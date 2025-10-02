import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import CallbackQuery, Message

# Import the handler. Ensure Python can find 'src' (e.g., run tests from project root or set PYTHONPATH)
from src.handlers.curiosities import show_curiosity_callback

@pytest.mark.asyncio
async def test_show_curiosity_callback_success():
    # 1. Arrange
    mock_callback = AsyncMock(spec=CallbackQuery)
    mock_callback.message = AsyncMock(spec=Message)
    mock_callback.message.answer = AsyncMock() # This should be called
    mock_callback.answer = AsyncMock() # This should also be called

    fake_curiosity = type('Obj', (object,), {
        'categoria': 'Gramática',
        'texto': 'Esta es una curiosidad de prueba.'
    })()

    # 2. Act & Assert
    # Patch the EXACT location where the handler looks for CuriosityService
    with patch('src.handlers.curiosities.CuriosityService.get_random_curiosity', return_value=fake_curiosity):
        await show_curiosity_callback(mock_callback, AsyncMock())

    # 3. Assert
    mock_callback.message.answer.assert_called_once()
    mock_callback.answer.assert_called_once()