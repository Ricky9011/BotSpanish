from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserExercise:
    id: int
    user_id: int
    exercise_id: int
    completed_at: datetime
    nivel: str
    categoria: str