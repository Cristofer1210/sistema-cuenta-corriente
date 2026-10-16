
from app.database.connection import transaction


def _texto_obligatorio(valor, campo):
    """Valida un texto obligatorio y elimina espacios sobrantes."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"El campo '{campo}' es obligatorio.")
    return valor.strip()


def _importe_valido(importe):
    """El precio se recibe como un entero expresado en centavos."""
    if isinstance(importe, bool) or not isinstance(importe, int):
        raise ValueError("El precio debe ser un entero en centavos.")
    if importe < 0:
        raise ValueError("El precio no puede ser negativo.")


def _cantidad_valida(cantidad, permitir_cero=True):
    if isinstance(cantidad, bool) or not isinstance(cantidad, int):
        raise ValueError("La cantidad debe ser un número entero.")

    minimo = 0 if permitir_cero else 1
    if cantidad < minimo:
        raise ValueError(
            f"La cantidad debe ser mayor o igual a {minimo}."
        )


def listar_productos(busqueda="", incluir_inactivos=False):
    """Lista productos con cantidad de variantes y stock total."""
    busqueda = busqueda.strip() if isinstance(busqueda, str) else ""

    sql = """
        SELECT
            p.id,
            p.nombre,
            p.categoria,
            p.precio_centavos,
            p.activo,
            p.creado_en,
            COUNT(v.id) AS cantidad_variantes,
            COALESCE(SUM(v.stock_actual), 0) AS stock_total
        FROM productos AS p
        LEFT JOIN variantes_producto AS v
            ON v.producto_id = p.id
    """

    condiciones = []
    parametros = []

    if not incluir_inactivos:
        condiciones.append("p.activo = 1")

    if busqueda:
        condiciones.append(
            "(p.nombre LIKE ? OR p.categoria LIKE ?)"
        )
        termino = f"%{busqueda}%"
        parametros.extend([termino, termino])

    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)

    sql += """
        GROUP BY p.id
        ORDER BY p.nombre COLLATE NOCASE
    """

    with transaction() as connection:
        return connection.execute(sql, parametros).fetchall()


def obtener_producto(producto_id):
    """Obtiene un producto por su identificador."""
    with transaction() as connection:
        return connection.execute(
            """
            SELECT *
            FROM productos
            WHERE id = ?
            """,
            (producto_id,),
        ).fetchone()


def crear_producto(nombre, categoria, precio_centavos):
    """Crea un producto y registra la acción en la auditoría."""
    nombre = _texto_obligatorio(nombre, "nombre")
    categoria = categoria.strip() if isinstance(categoria, str) else ""
    _importe_valido(precio_centavos)

    with transaction() as connection:
        cursor = connection.execute(
            """
            INSERT INTO productos (nombre, categoria, precio_centavos)
            VALUES (?, ?, ?)
            """,
            (nombre, categoria, precio_centavos),
        )

        producto_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO auditoria (
                entidad, entidad_id, accion, motivo, detalles
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "PRODUCTO",
                producto_id,
                "CREAR",
                "Alta de producto",
                f"Nombre: {nombre}; categoría: {categoria}; "
                f"precio_centavos: {precio_centavos}",
            ),
        )

    return producto_id


def editar_producto(
    producto_id,
    nombre,
    categoria,
    precio_centavos,
    motivo,
):
    """Modifica los datos comerciales y conserva la auditoría."""
    nombre = _texto_obligatorio(nombre, "nombre")
    motivo = _texto_obligatorio(motivo, "motivo de modificación")
    categoria = categoria.strip() if isinstance(categoria, str) else ""
    _importe_valido(precio_centavos)

    with transaction() as connection:
        anterior = connection.execute(
            """
            SELECT nombre, categoria, precio_centavos, activo
            FROM productos
            WHERE id = ?
            """,
            (producto_id,),
        ).fetchone()

        if anterior is None:
            raise ValueError("El producto no existe.")

        if not anterior["activo"]:
            raise ValueError("No se puede editar un producto inactivo.")

        connection.execute(
            """
            UPDATE productos
            SET nombre = ?, categoria = ?, precio_centavos = ?
            WHERE id = ?
            """,
            (nombre, categoria, precio_centavos, producto_id),
        )

        connection.execute(
            """
            INSERT INTO auditoria (
                entidad, entidad_id, accion, motivo, detalles
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "PRODUCTO",
                producto_id,
                "EDITAR",
                motivo,
                f"Anterior: nombre={anterior['nombre']}; "
                f"categoría={anterior['categoria']}; "
                f"precio_centavos={anterior['precio_centavos']}. "
                f"Nuevo: nombre={nombre}; categoría={categoria}; "
                f"precio_centavos={precio_centavos}.",
            ),
        )


def desactivar_producto(producto_id, motivo):
    """Desactiva el producto y sus variantes sin eliminar su historial."""
    motivo = _texto_obligatorio(motivo, "motivo de desactivación")

    with transaction() as connection:
        producto = connection.execute(
            """
            SELECT nombre, activo
            FROM productos
            WHERE id = ?
            """,
            (producto_id,),
        ).fetchone()

        if producto is None:
            raise ValueError("El producto no existe.")

        if not producto["activo"]:
            raise ValueError("El producto ya está inactivo.")

        connection.execute(
            "UPDATE productos SET activo = 0 WHERE id = ?",
            (producto_id,),
        )
        connection.execute(
            """
            UPDATE variantes_producto
            SET activo = 0
            WHERE producto_id = ?
            """,
            (producto_id,),
        )
        connection.execute(
            """
            INSERT INTO auditoria (
                entidad, entidad_id, accion, motivo, detalles
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "PRODUCTO",
                producto_id,
                "DESACTIVAR",
                motivo,
                f"Producto desactivado: {producto['nombre']}",
            ),
        )


def listar_variantes(producto_id, incluir_inactivas=False):
    """Lista los talles y colores de un producto."""
    sql = """
        SELECT
            id, producto_id, talle, color, stock_actual, activo
        FROM variantes_producto
        WHERE producto_id = ?
    """
    parametros = [producto_id]

    if not incluir_inactivas:
        sql += " AND activo = 1"

    sql += " ORDER BY talle COLLATE NOCASE, color COLLATE NOCASE"

    with transaction() as connection:
        return connection.execute(sql, parametros).fetchall()


def crear_variante(
    producto_id,
    talle,
    color,
    stock_inicial=0,
    motivo="Alta de variante",
):
    """Crea una combinación de talle y color con stock inicial auditado."""
    talle = talle.strip() if isinstance(talle, str) else ""
    color = color.strip() if isinstance(color, str) else ""
    motivo = _texto_obligatorio(motivo, "motivo")
    _cantidad_valida(stock_inicial)

    with transaction() as connection:
        producto = connection.execute(
            """
            SELECT nombre, activo
            FROM productos
            WHERE id = ?
            """,
            (producto_id,),
        ).fetchone()

        if producto is None:
            raise ValueError("El producto no existe.")

        if not producto["activo"]:
            raise ValueError("No se pueden agregar variantes a un producto inactivo.")

        cursor = connection.execute(
            """
            INSERT INTO variantes_producto (
                producto_id, talle, color, stock_actual
            )
            VALUES (?, ?, ?, ?)
            """,
            (producto_id, talle, color, stock_inicial),
        )

        variante_id = cursor.lastrowid

        if stock_inicial > 0:
            connection.execute(
                """
                INSERT INTO movimientos_stock (
                    variante_id, cambio, motivo, observaciones
                )
                VALUES (?, ?, 'SALDO_INICIAL', ?)
                """,
                (
                    variante_id,
                    stock_inicial,
                    motivo,
                ),
            )

        connection.execute(
            """
            INSERT INTO auditoria (
                entidad, entidad_id, accion, motivo, detalles
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "VARIANTE",
                variante_id,
                "CREAR",
                motivo,
                f"Producto: {producto['nombre']}; talle: {talle}; "
                f"color: {color}; stock inicial: {stock_inicial}",
            ),
        )

    return variante_id


def ajustar_stock(variante_id, cambio, motivo):
    """
    Ajusta el stock mediante un movimiento registrado.
    cambio positivo suma unidades; negativo resta unidades.
    """
    if isinstance(cambio, bool) or not isinstance(cambio, int):
        raise ValueError("El cambio de stock debe ser un número entero.")
    if cambio == 0:
        raise ValueError("El cambio de stock no puede ser cero.")
    motivo = _texto_obligatorio(motivo, "motivo del ajuste")

    with transaction() as connection:
        variante = connection.execute(
            """
            SELECT
                v.stock_actual,
                v.activo,
                p.activo AS producto_activo,
                p.nombre
            FROM variantes_producto AS v
            JOIN productos AS p ON p.id = v.producto_id
            WHERE v.id = ?
            """,
            (variante_id,),
        ).fetchone()

        if variante is None:
            raise ValueError("La variante no existe.")

        if not variante["activo"] or not variante["producto_activo"]:
            raise ValueError("No se puede ajustar el stock de una variante inactiva.")

        nuevo_stock = variante["stock_actual"] + cambio

        if nuevo_stock < 0:
            raise ValueError(
                f"Stock insuficiente. Stock disponible: "
                f"{variante['stock_actual']}."
            )

        connection.execute(
            """
            UPDATE variantes_producto
            SET stock_actual = ?
            WHERE id = ?
            """,
            (nuevo_stock, variante_id),
        )

        connection.execute(
            """
            INSERT INTO movimientos_stock (
                variante_id, cambio, motivo, observaciones
            )
            VALUES (?, ?, 'AJUSTE', ?)
            """,
            (variante_id, cambio, motivo),
        )

        connection.execute(
            """
            INSERT INTO auditoria (
                entidad, entidad_id, accion, motivo, detalles
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "VARIANTE",
                variante_id,
                "AJUSTAR_STOCK",
                motivo,
                f"Producto: {variante['nombre']}; "
                f"stock anterior: {variante['stock_actual']}; "
                f"cambio: {cambio}; stock nuevo: {nuevo_stock}",
            ),
        )

    return nuevo_stock
