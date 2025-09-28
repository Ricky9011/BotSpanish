# scripts/migrate_curiosities_only.py
import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Establece una conexión a la base de datos PostgreSQL utilizando las variables de entorno.
    """
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        return None


class CuriosityService:
    """Servicio simplificado para curiosidades (sin dependencias externas)"""

    @staticmethod
    def add_curiosity(categoria: str, texto: str) -> int:
        """Añade una nueva curiosidad a la base de datos"""
        conn = get_db_connection()
        if not conn:
            return -1

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO curiosidades (categoria, texto)
                    VALUES (%s, %s)
                    RETURNING id
                """, (categoria, texto))
                result = cursor.fetchone()
                conn.commit()
                return result[0] if result else -1
        except Exception as e:
            logger.error(f"Error al añadir curiosidad: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()

    @staticmethod
    def get_curiosity_count() -> int:
        """Cuenta cuántas curiosidades hay en la base de datos"""
        conn = get_db_connection()
        if not conn:
            return 0

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM curiosidades WHERE activo = TRUE")
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error al contar curiosidades: {e}")
            return 0
        finally:
            conn.close()


def load_curiosidades_from_json():
    """Carga las curiosidades desde el archivo JSON"""
    json_path = Path("curiosidades.json")

    if not json_path.exists():
        logger.error(f"No se encontró el archivo {json_path}")
        return []

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        curiosidades = data.get('curiosidades', [])
        logger.info(f"Se encontraron {len(curiosidades)} curiosidades en el JSON")
        return curiosidades

    except Exception as e:
        logger.error(f"Error al leer el archivo JSON: {e}")
        return []


def add_additional_curiosities():
    """Añade curiosidades adicionales para complementar las existentes"""
    additional_curiosities = [
        {
            "categoria": "gramática",
            "texto": "El español tiene dos formas de tratar a las personas: 'tú' (informal) y 'usted' (formal), lo que se conoce como distinción T-V."
        },
        {
            "categoria": "historia",
            "texto": "El primer diccionario de español fue publicado en 1611 por Sebastián de Covarrubias con el nombre 'Tesoro de la lengua castellana o española'."
        },
        {
            "categoria": "cultura",
            "texto": "El Día del Español se celebra el tercer sábado de junio en honor al idioma español en todo el mundo."
        },
        {
            "categoria": "vocabulario",
            "texto": "La palabra 'ojalá' viene del árabe 'inshallah' que significa 'si Dios quiere', mostrando la influencia árabe en el español."
        },
        {
            "categoria": "gramática",
            "texto": "El español tiene verbos irregulares que cambian su raíz en diferentes tiempos, como 'tener' (tengo, tienes, tuvo)."
        },
        {
            "categoria": "regionalismos",
            "texto": "En España, 'coche' significa automóvil, mientras que en América Latina generalmente se dice 'carro' o 'auto'."
        },
        {
            "categoria": "expresiones",
            "texto": "'Estar en la edad del pavo' significa estar en la adolescencia, una etapa de cambios e inseguridades."
        },
        {
            "categoria": "cultura",
            "texto": "El español es el idioma oficial de las Naciones Unidas, la Unión Europea y muchos otros organismos internacionales."
        },
        {
            "categoria": "historia",
            "texto": "El español moderno se standardizó en el siglo XIII con el Rey Alfonso X el Sabio, quien promovió su uso en documentos oficiales."
        },
        {
            "categoria": "gramática",
            "texto": "Los pronombres de objeto directo e indirecto en español (me, te, lo, la, le, nos, os, los, las, les) se colocan antes del verbo conjugado."
        }
    ]

    return additional_curiosities


def check_database_connection():
    """Verifica la conexión a la base de datos"""
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            logger.info("✅ Conexión a la base de datos establecida")
            return True
        else:
            logger.error("❌ No se pudo establecer conexión con la base de datos")
            return False
    except Exception as e:
        logger.error(f"❌ Error al conectar con la base de datos: {e}")
        return False


def check_table_exists():
    """Verifica que la tabla curiosidades exista"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'curiosidades'
                )
            """)
            exists = cursor.fetchone()[0]
            if exists:
                logger.info("✅ La tabla 'curiosidades' existe")
            else:
                logger.error("❌ La tabla 'curiosidades' no existe")
            return exists
    except Exception as e:
        logger.error(f"Error al verificar la tabla: {e}")
        return False
    finally:
        conn.close()


def create_table_if_not_exists():
    """Crea la tabla curiosidades si no existe"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS curiosidades (
                    id SERIAL PRIMARY KEY,
                    categoria VARCHAR(100) NOT NULL,
                    texto TEXT NOT NULL,
                    activo BOOLEAN DEFAULT TRUE,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("✅ Tabla 'curiosidades' verificada/creada correctamente")
            return True
    except Exception as e:
        logger.error(f"Error al crear la tabla: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_existing_curiosities():
    """Obtiene las curiosidades existentes en la base de datos para evitar duplicados"""
    existing_texts = set()
    conn = get_db_connection()
    if not conn:
        return set()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT texto FROM curiosidades")
            results = cursor.fetchall()
            for result in results:
                existing_texts.add(result[0].strip().lower())
        logger.info(f"Se encontraron {len(existing_texts)} curiosidades existentes en la BD")
        return existing_texts
    except Exception as e:
        logger.error(f"Error al obtener curiosidades existentes: {e}")
        return set()
    finally:
        conn.close()


def migrate_curiosities():
    """Migra las curiosidades desde JSON a la base de datos"""
    print("🚀 Iniciando migración de curiosidades desde JSON...")

    # Verificar conexión a la base de datos
    if not check_database_connection():
        return False

    # Crear tabla si no existe
    if not create_table_if_not_exists():
        return False

    try:
        # Contar curiosidades existentes antes de la migración
        count_before = CuriosityService.get_curiosity_count()
        logger.info(f"Curiosidades existentes antes de la migración: {count_before}")

        # Obtener textos existentes para evitar duplicados
        existing_texts = get_existing_curiosities()

        # Cargar curiosidades del JSON
        json_curiosities = load_curiosidades_from_json()

        # Añadir curiosidades adicionales
        additional_curiosities = add_additional_curiosities()

        all_curiosities = json_curiosities + additional_curiosities

        print(f"📚 Total de curiosidades a procesar: {len(all_curiosities)}")
        print(f"   - Del JSON: {len(json_curiosities)}")
        print(f"   - Adicionales: {len(additional_curiosities)}")

        # Insertar curiosidades
        inserted_count = 0
        skipped_count = 0
        error_count = 0

        for i, curiosidad in enumerate(all_curiosities, 1):
            categoria = curiosidad.get('categoria', 'general').strip().lower()
            texto = curiosidad.get('texto', '').strip()

            # Validar campos obligatorios
            if not texto:
                logger.warning(f"Curiosidad {i} sin texto, saltando...")
                skipped_count += 1
                continue

            if not categoria:
                categoria = "general"

            # Verificar si ya existe una curiosidad con el mismo texto (case-insensitive)
            if texto.lower() in existing_texts:
                logger.info(f"Curiosidad {i} ya existe, saltando...")
                skipped_count += 1
                continue

            # Insertar nueva curiosidad
            try:
                curiosity_id = CuriosityService.add_curiosity(categoria, texto)
                if curiosity_id != -1:
                    inserted_count += 1
                    existing_texts.add(texto.lower())  # Añadir a existentes para evitar duplicados en esta sesión
                    print(f"✅ [{i}/{len(all_curiosities)}] Insertada: {categoria} - {texto[:60]}...")
                else:
                    print(f"❌ [{i}/{len(all_curiosities)}] Error al insertar: {categoria}")
                    error_count += 1
            except Exception as e:
                print(f"❌ [{i}/{len(all_curiosities)}] Error: {e}")
                error_count += 1

        # Contar curiosidades después de la migración
        count_after = CuriosityService.get_curiosity_count()

        print(f"\n📊 RESUMEN DE LA MIGRACIÓN:")
        print(f"   • Curiosidades antes: {count_before}")
        print(f"   • Curiosidades después: {count_after}")
        print(f"   • Nuevas insertadas: {inserted_count}")
        print(f"   • Saltadas (duplicados): {skipped_count}")
        print(f"   • Errores: {error_count}")
        print(f"   • Total procesadas: {len(all_curiosities)}")

        if inserted_count > 0:
            print(f"🎉 ¡Migración completada exitosamente! Se añadieron {inserted_count} curiosidades.")

            # Mostrar estadísticas por categoría
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT categoria, COUNT(*) as cantidad 
                            FROM curiosidades 
                            WHERE activo = TRUE 
                            GROUP BY categoria 
                            ORDER BY cantidad DESC
                        """)
                        categorias = cursor.fetchall()

                        print(f"\n📈 DISTRIBUCIÓN POR CATEGORÍA:")
                        for categoria, cantidad in categorias:
                            print(f"   • {categoria}: {cantidad}")
                except Exception as e:
                    logger.error(f"Error al obtener estadísticas: {e}")
                finally:
                    conn.close()

        else:
            print("ℹ️  No se insertaron nuevas curiosidades (posiblemente ya existían todas).")

        return True

    except Exception as e:
        logger.error(f"Error en la migración: {e}", exc_info=True)
        return False


def main():
    """Función principal"""
    print("=" * 70)
    print("🚀 MIGRACIÓN DE CURIOSIDADES DESDE JSON")
    print("=" * 70)

    # Verificar variables de entorno
    required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Variables de entorno faltantes:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Asegúrate de tener un archivo .env con estas variables:")
        print("   DB_NAME=tu_base_de_datos")
        print("   DB_USER=tu_usuario")
        print("   DB_PASSWORD=tu_contraseña")
        print("   DB_HOST=localhost")
        print("   DB_PORT=5432")
        return

    # Migrar curiosidades desde JSON
    success = migrate_curiosities()

    print("\n" + "=" * 70)
    if success:
        print("✅ Proceso de migración completado exitosamente")
    else:
        print("❌ Hubo errores en el proceso de migración")
    print("=" * 70)


if __name__ == "__main__":
    main()