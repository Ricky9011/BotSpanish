from dataclasses import dataclass

class Curiosity:
    def __init__(self, id: int, categoria: str, texto: str, activo: bool = True):
        self.id = id
        self.categoria = categoria
        self.texto = texto  # Esta propiedad debe existir
        self.activo = activo