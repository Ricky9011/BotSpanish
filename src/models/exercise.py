from dataclasses import dataclass
from typing import List


@dataclass
class Exercise:
    id: int
    categoria: str
    nivel: str
    pregunta: str
    opciones: List[str]
    respuesta_correcta: int
    explicacion: str = None

    def to_dict(self):
        return {
            "id": self.id,
            "categoria": self.categoria,
            "nivel": self.nivel,
            "pregunta": self.pregunta,
            "opciones": self.opciones,
            "respuesta_correcta": self.respuesta_correcta,
            "explicacion": self.explicacion
        }