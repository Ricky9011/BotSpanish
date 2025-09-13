import re

def sanitize_text(text: str, max_length=200) -> str:
    """Escapa caracteres especiales y limita la longitud del texto"""
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

def validate_input(text: str, max_length=1000) -> str:
    """Valida y limpia la entrada del usuario"""
    if len(text) > max_length:
        raise ValueError("La entrada es demasiado larga")
    return sanitize_text(text)