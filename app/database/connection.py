
from contextlib import contextmanager
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "softtech.db"


def get_connection() -> sqlite3.Connection:
    """Abre una conexión SQLite con las claves foráneas habilitadas."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")

    return connection


@contextmanager
def transaction():
    """Confirma todos los cambios juntos o los revierte si hay un error."""
    connection = get_connection()

    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database():
    """Crea la base y aplica el esquema inicial."""
    from app.database.schema import initialize_schema

    connection = get_connection()

    try:
        initialize_schema(connection)
    finally:
        connection.close()
