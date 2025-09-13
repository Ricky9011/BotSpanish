import os
import re
import logging
from typing import Optional

def sanitize_text(text: str, max_length: int = 200) -> str:
    """
    Escapa caracteres especiales y limita la longitud del texto
    """
    if not text:
        return ""

    # Escapar caracteres especiales de Markdown
    text = re.sub(r"([_*\[\]()~`>#+\-=|{}\.!])", r"\\\1", text)

    # Eliminar posibles inyecciones SQL
    text = re.sub(r"[;\-\-]", "", text)

    # Limitar longitud
    if len(text) > max_length:
        text = text[:max_length-3] + "..."

    return text

def validate_input(text: str, max_length: int = 1000) -> str:
    """
    Valida y limpia la entrada del usuario
    """
    if len(text) > max_length:
        raise ValueError("La entrada es demasiado larga")
    return sanitize_text(text)

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configura el sistema de logging
    """
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, log_level.upper(), logging.INFO)
    )

def get_reply_func(update) -> Optional[callable]:
    """
    Obtiene la función de respuesta apropiada según el contexto
    """
    if hasattr(update, 'message') and update.message:
        return update.message.reply_text
    elif hasattr(update, 'callback_query') and update.callback_query and update.callback_query.message:
        return update.callback_query.message.reply_text
    elif hasattr(update, 'effective_message') and update.effective_message:
        return update.effective_message.reply_text
    return None

def is_admin(user_id: int) -> bool:
    return user_id == int(os.getenv("ADMIN_USER_ID", 0))

def generate_progress_bar(percentage: int) -> str:
    filled = '▓' * int(percentage / 5)
    empty = '░' * (20 - len(filled))
    return f"{filled}{empty} {percentage}%"