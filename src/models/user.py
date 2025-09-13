from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    user_id: int
    username: Optional[str]
    level: str = "principiante"
    exercises: int = 0
    referrals: int = 0
    challenge_score: int = 0
    streak_days: int = 0
    completed_exercises: str = ""
    last_practice: Optional[str] = None

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "level": self.level,
            "exercises": self.exercises,
            "referrals": self.referrals,
            "challenge_score": self.challenge_score,
            "streak_days": self.streak_days,
            "completed_exercises": self.completed_exercises,
            "last_practice": self.last_practice
        }