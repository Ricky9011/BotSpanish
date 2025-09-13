import unittest
from src.models.user import User
from src.models.exercise import Exercise
from src.models.curiosity import Curiosity

class TestModels(unittest.TestCase):
    def test_user_model(self):
        user = User(
            user_id=2006572428,
            username="test_user",
            level="principiante",
            exercises=5,
            referrals=2,
            challenge_score=100,
            streak_days=3,
            completed_exercises="1,2,3",
            last_practice="2025-09-10 15:00:00"
        )
        self.assertEqual(user.user_id, 2006572428)
        self.assertEqual(user.username, "test_user")
        self.assertEqual(user.level, "principiante")
        self.assertEqual(user.exercises, 5)
        self.assertEqual(user.completed_exercises, "1,2,3")

    def test_exercise_model(self):
        exercise = Exercise(
            id=1,
            categoria="Gramática",
            nivel="principiante",
            pregunta="¿Cuál es el verbo correcto?",
            opciones='["es","somos","son"]',
            respuesta_correcta=0,
            explicacion="Es el correcto para la tercera persona singular."
        )
        self.assertEqual(exercise.id, 1)
        self.assertEqual(exercise.categoria, "Gramática")
        self.assertEqual(exercise.nivel, "principiante")
        self.assertEqual(exercise.opciones, '["es","somos","son"]')

    def test_curiosity_model(self):
        curiosity = Curiosity(id=1, categoria="Cultura", texto="El español es hablado por más de 500 millones de personas.")
        self.assertEqual(curiosity.id, 1)
        self.assertEqual(curiosity.categoria, "Cultura")
        self.assertEqual(curiosity.texto, "El español es hablado por más de 500 millones de personas.")

if __name__ == "__main__":
    unittest.main()