
from app.database.connection import (
    initialize_database,
    get_connection,
    DATABASE_PATH,
)


def main():
    print("Inicializando la base de datos...")

    initialize_database()

    with get_connection() as connection:
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        foreign_keys = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

    print(f"\nBase de datos: {DATABASE_PATH}")
    print("\nTablas creadas:")

    for table in tables:
        print(f" - {table['name']}")

    print(f"\nClaves foráneas habilitadas: {foreign_keys}")

    if foreign_keys != 1:
        raise RuntimeError("Las claves foráneas no están habilitadas.")

    print("\nBase de datos inicializada correctamente.")


if __name__ == "__main__":
    main()
