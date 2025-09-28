# src/handlers/__init__.py
from .commands import router as commands_router
from .exercises import router as exercises_router
from .curiosities import router as curiosities_router
from .nivel import router as nivel_router


__all__ = [
    'commands_router',
    'exercises_router',
    'curiosities_router',
    'nivel_router'
]