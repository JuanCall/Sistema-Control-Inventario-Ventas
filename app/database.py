from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Indicamos la ruta del archivo SQLite
# Como ejecutaremos el servidor desde la carpeta principal, buscamos en el directorio raíz (./)
SQLALCHEMY_DATABASE_URL = "sqlite:///./inventario.db"

# 2. Creamos el "motor" de conexión
# El check_same_thread es una configuración especial necesaria cuando usamos SQLite con FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Configuramos la sesión (la vía por donde enviaremos datos a la base de datos)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Creamos la clase Base. De aquí nacerán nuestras tablas en versión Python.
Base = declarative_base()