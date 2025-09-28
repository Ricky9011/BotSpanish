# models/curiosity.py - VERSIÓN CORREGIDA
from dataclasses import dataclass

@dataclass
class Curiosity:
    id: int
    categoria: str
    texto: str
    activo: bool = True

    def __init__(self, id: int, categoria: str, texto: str, activo: bool = True):
        self.id = id
        self.categoria = categoria
        self.texto = texto  # ✅ Propiedad correcta
        self.activo = activo

    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'categoria': self.categoria,
            'texto': self.texto,
            'activo': self.activo
        }