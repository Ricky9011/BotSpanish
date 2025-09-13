import json
import ast
import logging
from typing import Dict, List, Any
from src.services.database import DatabaseService

logger = logging.getLogger(__name__)


class ImportService:
    @staticmethod
    def normalize_json_data(data: Any) -> str:
        """
        Normaliza datos para asegurar que sean JSON válido
        """
        if data is None:
            return json.dumps([])

        # Si ya es una cadena JSON válida, devolverla
        if isinstance(data, str):
            try:
                json.loads(data)
                return data
            except json.JSONDecodeError:
                pass

        # Intentar con ast.literal_eval para literales de Python
        if isinstance(data, str):
            try:
                parsed = ast.literal_eval(data)
                return json.dumps(parsed, ensure_ascii=False)
            except (ValueError, SyntaxError):
                pass

        # Si es una cadena simple, convertirla a array
        if isinstance(data, str):
            return json.dumps([data], ensure_ascii=False)

        # Si es una lista o diccionario, convertirlo a JSON
        if isinstance(data, (list, dict)):
            return json.dumps(data, ensure_ascii=False)

        # Para cualquier otro tipo, convertirlo a string y luego a array
        return json.dumps([str(data)], ensure_ascii=False)

    @staticmethod
    def import_exercises_from_json(json_data: Dict) -> Dict[str, int]:
        """
        Importa ejercicios desde un objeto JSON
        Retorna un diccionario con estadísticas de la importación
        """
        stats = {
            "total": 0,
            "success": 0,
            "errors": 0,
            "skipped": 0
        }

        try:
            for nivel, categorias in json_data.items():
                for categoria, ejercicios in categorias.items():
                    for ejercicio in ejercicios:
                        stats["total"] += 1

                        try:
                            # Normalizar las opciones
                            opciones_normalizadas = ImportService.normalize_json_data(
                                ejercicio.get("opciones", [])
                            )

                            # Insertar en la base de datos
                            DatabaseService.add_exercise(
                                categoria=categoria,
                                nivel=nivel,
                                pregunta=ejercicio["pregunta"],
                                opciones=opciones_normalizadas,
                                respuesta_correcta=ejercicio["respuesta"],
                                explicacion=ejercicio.get("explicacion")
                            )

                            stats["success"] += 1
                            logger.info(f"Ejercicio importado: {ejercicio['pregunta'][:50]}...")

                        except Exception as e:
                            stats["errors"] += 1
                            logger.error(f"Error importando ejercicio: {e}")

        except Exception as e:
            logger.error(f"Error procesando JSON: {e}")
            stats["errors"] += 1

        return stats

    @staticmethod
    def import_curiosities_from_json(json_data: Dict) -> Dict[str, int]:
        """
        Importa curiosidades desde un objeto JSON
        Retorna un diccionario con estadísticas de la importación
        """
        stats = {
            "total": 0,
            "success": 0,
            "errors": 0,
            "skipped": 0
        }

        try:
            curiosidades = json_data.get("curiosidades", [])
            stats["total"] = len(curiosidades)

            for curiosidad in curiosidades:
                try:
                    DatabaseService.add_curiosity(
                        categoria=curiosidad["categoria"],
                        texto=curiosidad["texto"]
                    )
                    stats["success"] += 1
                    logger.info(f"Curiosidad importada: {curiosidad['texto'][:50]}...")

                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"Error importando curiosidad: {e}")

        except Exception as e:
            logger.error(f"Error procesando JSON de curiosidades: {e}")
            stats["errors"] += 1

        return stats