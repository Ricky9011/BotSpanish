# src/utils/exercise_utils.py
import json
from pathlib import Path
from typing import List, Dict, Any


def validate_exercises_json(json_path: str) -> List[str]:
    """
    Valida la estructura y contenido de un archivo JSON de ejercicios.

    Args:
        json_path (str): Ruta al archivo JSON

    Returns:
        List[str]: Lista de errores encontrados, vacía si no hay errores
    """
    errors = []

    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        return [f"Error de formato JSON: {str(e)}"]
    except FileNotFoundError:
        return [f"Archivo no encontrado: {json_path}"]
    except Exception as e:
        return [f"Error al leer el archivo: {str(e)}"]

    # Verificar estructura básica
    if not isinstance(data, dict):
        errors.append("El JSON debe ser un objeto con niveles (principiante, intermedio, avanzado)")
        return errors

    # Verificar niveles
    valid_levels = ["principiante", "intermedio", "avanzado"]
    for nivel in data.keys():
        if nivel not in valid_levels:
            errors.append(f"Nivel inválido: {nivel}. Debe ser uno de: {', '.join(valid_levels)}")

    for nivel, categorias in data.items():
        if not isinstance(categorias, dict):
            errors.append(f"El nivel '{nivel}' debe contener categorías")
            continue

        for categoria, ejercicios in categorias.items():
            if not isinstance(ejercicios, list):
                errors.append(f"La categoría '{categoria}' en nivel '{nivel}' debe ser una lista de ejercicios")
                continue

            for i, ejercicio in enumerate(ejercicios):
                # Verificar campos obligatorios
                if "pregunta" not in ejercicio:
                    errors.append(f"Ejercicio sin pregunta en {nivel}/{categoria}[{i}]")

                if "opciones" not in ejercicio:
                    errors.append(f"Ejercicio sin opciones en {nivel}/{categoria}[{i}]")

                if "respuesta" not in ejercicio:
                    errors.append(f"Ejercicio sin respuesta en {nivel}/{categoria}[{i}]")

                # Verificar tipos de datos
                if "pregunta" in ejercicio and not isinstance(ejercicio["pregunta"], str):
                    errors.append(f"Pregunta debe ser texto en {nivel}/{categoria}[{i}]")

                if "opciones" in ejercicio and (not isinstance(ejercicio["opciones"], list) or
                                                not all(isinstance(op, str) for op in ejercicio["opciones"])):
                    errors.append(f"Opciones debe ser una lista de textos en {nivel}/{categoria}[{i}]")

                if "respuesta" in ejercicio and not isinstance(ejercicio["respuesta"], int):
                    errors.append(f"Respuesta debe ser un número entero en {nivel}/{categoria}[{i}]")

                # Verificar que la respuesta sea válida
                if "opciones" in ejercicio and "respuesta" in ejercicio:
                    if ejercicio["respuesta"] < 0 or ejercicio["respuesta"] >= len(ejercicio["opciones"]):
                        errors.append(
                            f"Respuesta inválida en {nivel}/{categoria}[{i}]: {ejercicio['respuesta']} (debe estar entre 0 y {len(ejercicio['opciones']) - 1})")

    return errors


def load_exercises_from_json(json_path: str) -> Dict[str, Any]:
    """
    Carga ejercicios desde un archivo JSON validado.

    Args:
        json_path (str): Ruta al archivo JSON

    Returns:
        Dict[str, Any]: Datos de ejercicios cargados

    Raises:
        ValueError: Si el JSON no pasa la validación
    """
    errors = validate_exercises_json(json_path)
    if errors:
        raise ValueError(f"Errores en el JSON:\n" + "\n".join(errors))

    with open(json_path, 'r', encoding='utf-8') as file:
        return json.load(file)