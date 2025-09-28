# services/curiosity_service.py - VERSIÓN CORREGIDA
import logging
from src.models.curiosity import Curiosity
from src.services.database import DatabaseService

logger = logging.getLogger(__name__)


class CuriosityService:

    @staticmethod
    def get_random_curiosity():
        """Obtiene una curiosidad aleatoria activa - VERSIÓN CORREGIDA"""
        try:
            with DatabaseService.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, categoria, texto 
                    FROM curiosidades 
                    WHERE activo = TRUE 
                    ORDER BY RANDOM() 
                    LIMIT 1
                """)

                result = cursor.fetchone()
                logger.info(f"Consulta BD curiosidad - Resultado: {result is not None}")

                if result:
                    # ✅ Asegurar que tenemos exactamente 3 valores
                    curiosity_id, categoria, texto = result
                    return Curiosity(id=curiosity_id, categoria=categoria, texto=texto)
                else:
                    logger.warning("No se encontraron curiosidades activas en la BD")
                    return None

        except Exception as e:
            logger.error(f"Error al obtener curiosidad aleatoria: {e}", exc_info=True)
            return None

    @staticmethod
    def get_curiosity_count() -> int:
        """Cuenta cuántas curiosidades activas hay disponibles"""
        try:
            with DatabaseService.get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM curiosidades WHERE activo = TRUE")
                result = cursor.fetchone()
                count = result[0] if result else 0
                logger.info(f"Conteo de curiosidades: {count}")
                return count
        except Exception as e:
            logger.error(f"Error al contar curiosidades: {e}")
            return 0