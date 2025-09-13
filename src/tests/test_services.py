import unittest
import asyncio
from unittest.mock import MagicMock, patch
from src.services.database import DatabaseService
from src.services.user_service import UserService
from src.models.exercise import Exercise
from src.models.curiosity import Curiosity

class TestServices(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        DatabaseService._connection_pool = MagicMock()

    @patch("src.services.database.DatabaseService.get_cursor")
    def test_user_service_register_user(self, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        UserService.register_user(2006572428, "test_user")
        mock_cursor.execute.assert_called_once()
        self.assertIn("INSERT INTO users", mock_cursor.execute.call_args[0][0])

    @patch("src.services.database.DatabaseService.get_cursor")
    def test_user_service_get_user_level(self, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["intermedio"]
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        level = UserService.get_user_level(2006572428)
        self.assertEqual(level, "intermedio")
        mock_cursor.execute.assert_called_once_with(
            "SELECT level FROM users WHERE user_id = %s", (2006572428,)
        )

    @patch("src.services.database.DatabaseService.get_cursor")
    def test_database_service_get_random_exercise(self, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            1, "Gramática", "principiante", "¿Cuál es el verbo correcto?", '["es","somos","son"]', 0, "Explicación"
        )
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        exercise = DatabaseService.get_random_exercise("principiante")
        self.assertIsInstance(exercise, Exercise)
        self.assertEqual(exercise.id, 1)
        self.assertEqual(exercise.nivel, "principiante")

    @patch("src.services.database.DatabaseService.get_cursor")
    def test_database_service_get_random_curiosity(self, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, "Cultura", "El español es hablado por más de 500 millones.")
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        curiosity = DatabaseService.get_random_curiosity()
        self.assertIsInstance(curiosity, Curiosity)
        self.assertEqual(curiosity.id, 1)
        self.assertEqual(curiosity.categoria, "Cultura")

    def test_all(self):
        self.test_user_service_register_user()
        self.test_user_service_get_user_level()
        self.test_database_service_get_random_exercise()
        self.test_database_service_get_random_curiosity()

if __name__ == "__main__":
    unittest.main()