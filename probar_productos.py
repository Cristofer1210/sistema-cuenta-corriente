
from app.database.connection import initialize_database
from app.services.productos_service import (
    crear_producto,
    crear_variante,
    ajustar_stock,
    listar_productos,
    listar_variantes,
)


def main():
    initialize_database()

    # Datos de prueba identificados expresamente como ficticios.
    producto_id = crear_producto(
        nombre="DEMO - Remera de prueba",
        categoria="DEMO",
        precio_centavos=1250000,
    )

    variante_id = crear_variante(
        producto_id=producto_id,
        talle="M",
        color="Negro",
        stock_inicial=5,
        motivo="Prueba técnica ficticia",
    )

    stock_final = ajustar_stock(
        variante_id=variante_id,
        cambio=2,
        motivo="Prueba técnica ficticia",
    )

    print("\nProductos registrados:")
    for producto in listar_productos("DEMO"):
        print(
            f"ID: {producto['id']} | "
            f"{producto['nombre']} | "
            f"Precio: ${producto['precio_centavos'] / 100:.2f} | "
            f"Stock: {producto['stock_total']}"
        )

    print("\nVariantes:")
    for variante in listar_variantes(producto_id):
        print(
            f"Talle: {variante['talle']} | "
            f"Color: {variante['color']} | "
            f"Stock: {variante['stock_actual']}"
        )

    print(f"\nStock final esperado: 7 | Obtenido: {stock_final}")
    print("\nPrueba finalizada.")


if __name__ == "__main__":
    main()
