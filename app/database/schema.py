
SCHEMA_VERSION = 1


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    telefono TEXT NOT NULL DEFAULT '',
    direccion TEXT NOT NULL DEFAULT '',
    observaciones TEXT NOT NULL DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    categoria TEXT NOT NULL DEFAULT '',
    precio_centavos INTEGER NOT NULL CHECK (precio_centavos >= 0),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS variantes_producto (
    id INTEGER PRIMARY KEY,
    producto_id INTEGER NOT NULL,
    talle TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    stock_actual INTEGER NOT NULL DEFAULT 0 CHECK (stock_actual >= 0),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    UNIQUE (producto_id, talle, color)
);

CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY,
    numero TEXT NOT NULL UNIQUE,
    cliente_id INTEGER,
    tipo TEXT NOT NULL CHECK (tipo IN ('CONTADO', 'CUENTA_CORRIENTE')),
    fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    total_centavos INTEGER NOT NULL DEFAULT 0 CHECK (total_centavos >= 0),
    estado TEXT NOT NULL DEFAULT 'BORRADOR'
        CHECK (estado IN ('BORRADOR', 'CONFIRMADA', 'ANULADA')),
    observaciones TEXT NOT NULL DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    CHECK (tipo != 'CUENTA_CORRIENTE' OR cliente_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS detalle_venta (
    id INTEGER PRIMARY KEY,
    venta_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    descripcion_snapshot TEXT NOT NULL,
    talle_snapshot TEXT NOT NULL DEFAULT '',
    color_snapshot TEXT NOT NULL DEFAULT '',
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario_centavos INTEGER NOT NULL
        CHECK (precio_unitario_centavos >= 0),
    subtotal_centavos INTEGER NOT NULL CHECK (subtotal_centavos >= 0),
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (variante_id) REFERENCES variantes_producto(id)
);

CREATE TABLE IF NOT EXISTS obligaciones (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    venta_id INTEGER UNIQUE,
    tipo TEXT NOT NULL
        CHECK (tipo IN ('VENTA', 'SALDO_INICIAL', 'AJUSTE')),
    descripcion TEXT NOT NULL DEFAULT '',
    fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    importe_centavos INTEGER NOT NULL CHECK (importe_centavos > 0),
    estado TEXT NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('ACTIVA', 'ANULADA')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (venta_id) REFERENCES ventas(id)
);

CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY,
    numero TEXT NOT NULL UNIQUE,
    cliente_id INTEGER NOT NULL,
    fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    importe_centavos INTEGER NOT NULL CHECK (importe_centavos > 0),
    medio TEXT NOT NULL DEFAULT 'OTRO'
        CHECK (medio IN ('EFECTIVO', 'TRANSFERENCIA', 'DEBITO',
                         'CREDITO', 'OTRO')),
    observaciones TEXT NOT NULL DEFAULT '',
    estado TEXT NOT NULL DEFAULT 'CONFIRMADO'
        CHECK (estado IN ('CONFIRMADO', 'ANULADO')),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE IF NOT EXISTS imputaciones_pago (
    id INTEGER PRIMARY KEY,
    pago_id INTEGER NOT NULL,
    obligacion_id INTEGER NOT NULL,
    importe_centavos INTEGER NOT NULL CHECK (importe_centavos > 0),
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (pago_id) REFERENCES pagos(id),
    FOREIGN KEY (obligacion_id) REFERENCES obligaciones(id),
    UNIQUE (pago_id, obligacion_id)
);

CREATE TABLE IF NOT EXISTS movimientos_stock (
    id INTEGER PRIMARY KEY,
    variante_id INTEGER NOT NULL,
    cambio INTEGER NOT NULL CHECK (cambio != 0),
    motivo TEXT NOT NULL CHECK (
        motivo IN ('SALDO_INICIAL', 'VENTA', 'DEVOLUCION',
                   'AJUSTE', 'ANULACION_VENTA')
    ),
    venta_id INTEGER,
    observaciones TEXT NOT NULL DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (variante_id) REFERENCES variantes_producto(id),
    FOREIGN KEY (venta_id) REFERENCES ventas(id)
);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY,
    entidad TEXT NOT NULL,
    entidad_id INTEGER,
    accion TEXT NOT NULL,
    motivo TEXT NOT NULL DEFAULT '',
    detalles TEXT NOT NULL DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_clientes_nombre
    ON clientes(nombre);

CREATE INDEX IF NOT EXISTS idx_productos_nombre
    ON productos(nombre);

CREATE INDEX IF NOT EXISTS idx_variantes_producto
    ON variantes_producto(producto_id);

CREATE INDEX IF NOT EXISTS idx_ventas_cliente_fecha
    ON ventas(cliente_id, fecha);

CREATE INDEX IF NOT EXISTS idx_obligaciones_cliente_fecha
    ON obligaciones(cliente_id, fecha);

CREATE INDEX IF NOT EXISTS idx_pagos_cliente_fecha
    ON pagos(cliente_id, fecha);

CREATE INDEX IF NOT EXISTS idx_imputaciones_obligacion
    ON imputaciones_pago(obligacion_id);

CREATE INDEX IF NOT EXISTS idx_movimientos_variante_fecha
    ON movimientos_stock(variante_id, creado_en);
"""


def initialize_schema(connection):
    """Aplica el esquema inicial sin borrar las tablas existentes."""
    connection.executescript(SCHEMA_SQL)

    connection.execute(
        """
        INSERT OR IGNORE INTO schema_version (version)
        VALUES (?)
        """,
        (SCHEMA_VERSION,),
    )
    connection.commit()
