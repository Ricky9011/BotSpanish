from dataclasses import dataclass


@dataclass
class Curiosity:
    id: int
    categoria: str
    texto: str

    def to_dict(self):
        return {
            "id": self.id,
            "categoria": self.categoria,
            "texto": self.texto
        }