# src/tests/test_handlers.py
import unittest
import asyncio
from unittest.mock import AsyncMock, patch, Mock
from aiogram.types import Message, User
from aiogram.fsm.context import FSMContext

# Import the actual handler functions
from src.handlers.commands import cmd_start, cmd_help
from src.handlers.feedback import cmd_feedback_button


class TestCommandsHandler(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Create a mock user
        self.user = Mock(spec=User)
        self.user.id = 2006572428
        self.user.username = "test_user"
        self.user.first_name = "Test"

        # Create a mock message with from_user
        self.message = AsyncMock(spec=Message)
        self.message.from_user = self.user
        self.message.answer = AsyncMock()  # Mock the answer method

        # Create a mock state for handlers that need it
        self.state = AsyncMock(spec=FSMContext)
        self.state.set_state = AsyncMock()
        self.state.clear = AsyncMock()

    def test_cmd_start(self):
        async def run_test():
            with patch("src.handlers.commands.UserService.register_user") as mock_register, \
                    patch("src.handlers.commands.MainMenuKeyboard.build", new_callable=AsyncMock) as mock_build:
                mock_build.return_value = "mock_keyboard"

                await cmd_start(self.message)

                mock_register.assert_called_once_with(2006572428, "test_user")
                self.message.answer.assert_called_once()
                self.assertIn("¡Hola Test!", self.message.answer.call_args[0][0])

        self.loop.run_until_complete(run_test())

    def test_cmd_help(self):
        async def run_test():
            await cmd_help(self.message)

            self.message.answer.assert_called_once()
            self.assertIn("Comandos Disponibles", self.message.answer.call_args[0][0])

        self.loop.run_until_complete(run_test())

    def test_cmd_feedback_button(self):
        async def run_test():
            await cmd_feedback_button(self.message, self.state)

            self.message.answer.assert_called_once_with(
                "📝 Por favor, escribe tu opinión, sugerencia o reporte de error.",
                parse_mode="Markdown"
            )
            self.state.set_state.assert_called_once()

        self.loop.run_until_complete(run_test())

    def tearDown(self):
        self.loop.close()


if __name__ == "__main__":
    unittest.main()