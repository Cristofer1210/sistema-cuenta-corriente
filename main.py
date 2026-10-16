
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QInputDialog,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFrame,
    QHBoxLayout,
)

from app.database.connection import initialize_database
from app.services.productos_service import (
    ajustar_stock,
    crear_producto,
    crear_variante,
    desactivar_producto,
    editar_producto,
    listar_productos,
    listar_variantes,
)


STYLE = """
QMainWindow, QWidget#content {
    background-color: #f4f7fb;
    color: #172033;
    font-family: Segoe UI;
    font-size: 13px;
}
QFrame#sidebar {
    background-color: #14213d;
    border: none;
}
QLabel#brand {
    color: white;
    font-size: 23px;
    font-weight: 700;
}
QLabel#brand_subtitle {
    color: #a9bad8;
    font-size: 10px;
    font-weight: 600;
}
QPushButton#nav {
    background: transparent;
    color: #d6dfef;
    border: none;
    border-radius: 7px;
    text-align: left;
    padding: 12px 14px;
    font-size: 13px;
}
QPushButton#nav:hover {
    background: #243657;
    color: white;
}
QPushButton#nav[active="true"] {
    background: #315ee8;
    color: white;
    font-weight: 600;
}
QLabel#page_title {
    font-size: 25px;
    font-weight: 700;
    color: #172554;
}
QLabel#muted {
    color: #64748b;
}
QFrame#card {
    background: white;
    border: 1px solid #e3e9f2;
    border-radius: 12px;
}
QLabel#metric_label {
    color: #64748b;
    font-size: 12px;
}
QLabel#metric_value {
    color: #172554;
    font-size: 25px;
    font-weight: 700;
}
QPushButton#primary {
    background: #315ee8;
    color: white;
    border: none;
    border-radius: 7px;
    padding: 10px 15px;
    font-weight: 600;
}
QPushButton#primary:hover {
    background: #244bc4;
}
QLineEdit {
    background-color: #ffffff;
    color: #172033;
    border: 1px solid #dbe3ef;
    border-radius: 7px;
    padding: 10px;
    selection-background-color: #315ee8;
    selection-color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #315ee8;
}
QTableWidget {
    color: #172033;
    background-color: #ffffff;
    alternate-background-color: #f8faff;
    selection-background-color: #dce7ff;
    selection-color: #172033;
    border: 1px solid #e3e9f2;
    border-radius: 8px;
    gridline-color: #edf1f7;
}
QTableWidget::item {
    color: #172033;
}
QHeaderView::section {
    color: #334155;
    background: #f1f5fb;
    padding: 11px 8px;
    border: none;
    border-bottom: 1px solid #dfe6f0;
    font-weight: 600;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SoftTech | Cuenta Corriente")
        self.resize(1320, 820)
        self.setMinimumSize(1050, 680)
        self.setStyleSheet(STYLE)

        self.pages = QStackedWidget()
        self.nav_buttons = {}

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = self.build_sidebar()
        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 25, 30, 25)
        content_layout.setSpacing(20)
        content_layout.addWidget(self.build_topbar())
        content_layout.addWidget(self.pages, 1)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)

        self.add_dashboard()
        self.add_products_page()
        self.add_table_page(
            "Clientes",
            "Datos de clientes y seguimiento de sus saldos.",
            ["Cliente", "Teléfono", "Saldo pendiente", "Estado"],
            [
                ["Cliente demostración 1", "—", "$ 24.000", "Pendiente"],
                ["Cliente demostración 2", "—", "$ 12.500", "Pendiente"],
                ["Cliente demostración 3", "—", "$ 0", "Al día"],
            ],
        )
        self.add_table_page(
            "Ventas",
            "Consulta de operaciones y comprobantes internos.",
            ["N.º", "Fecha", "Cliente", "Tipo", "Total", "Estado"],
            [
                ["DEMO-001", "15/10/2026", "Cliente demostración 1",
                 "Cuenta corriente", "$ 24.000", "Ejemplo"],
                ["DEMO-002", "15/10/2026", "Venta de mostrador",
                 "Contado", "$ 12.000", "Ejemplo"],
            ],
        )
        self.add_table_page(
            "Cuentas corrientes",
            "Saldos pendientes y seguimiento de pagos.",
            ["Cliente", "Saldo inicial", "Pagos", "Saldo pendiente"],
            [
                ["Cliente demostración 1", "$ 30.000", "$ 6.000", "$ 24.000"],
                ["Cliente demostración 2", "$ 12.500", "$ 0", "$ 12.500"],
            ],
        )
        self.add_table_page(
            "Reportes y comprobantes",
            "Acceso a reportes, tickets y estados de cuenta.",
            ["Documento", "Descripción", "Disponibilidad"],
            [
                ["Ticket interno", "Comprobante de venta", "Pendiente de implementar"],
                ["Estado de cuenta", "Detalle de deuda y pagos", "Pendiente de implementar"],
                ["Copia de seguridad", "Respaldo de la base de datos", "Pendiente de implementar"],
            ],
        )

        self.navigate("Inicio")

    def build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(235)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 24, 15, 18)
        layout.setSpacing(7)

        brand = QLabel("SoftTech")
        brand.setObjectName("brand")
        subtitle = QLabel("GESTIÓN DE INDUMENTARIA")
        subtitle.setObjectName("brand_subtitle")

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(28)

        nav_items = [
            ("Inicio", "▦"),
            ("Productos", "□"),
            ("Clientes", "♙"),
            ("Ventas", "↗"),
            ("Cuentas corrientes", "≡"),
            ("Reportes y comprobantes", "▤"),
        ]

        for name, symbol in nav_items:
            button = QPushButton(f"  {symbol}    {name}")
            button.setObjectName("nav")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setProperty("active", False)
            button.clicked.connect(
                lambda checked=False, page=name: self.navigate(page)
            )
            self.nav_buttons[name] = button
            layout.addWidget(button)

        layout.addStretch()

        demo = QLabel(
            "CATÁLOGO CONECTADO\n"
            "Productos guardados en SQLite\n"
            "Otras secciones: demostración"
        )
        demo.setStyleSheet(
            "color: #a9bad8; font-size: 10px; padding: 8px;"
        )
        demo.setWordWrap(True)
        layout.addWidget(demo)

        return sidebar

    def build_topbar(self):
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)

        context = QVBoxLayout()
        heading = QLabel("Panel de gestión")
        heading.setStyleSheet("font-size: 17px; font-weight: 600;")
        subtitle = QLabel("SoftTech Cuenta Corriente")
        subtitle.setObjectName("muted")
        context.addWidget(heading)
        context.addWidget(subtitle)

        status = QLabel("●  PROTOTIPO")
        status.setStyleSheet(
            "color: #9a6700; background: #fff4d6;"
            "padding: 8px 12px; border-radius: 7px; font-weight: 600;"
        )

        layout.addLayout(context)
        layout.addStretch()
        layout.addWidget(status)
        return bar

    def make_card(self, label, value, note):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 17, 18, 17)
        layout.setSpacing(9)

        title = QLabel(label)
        title.setObjectName("metric_label")
        number = QLabel(value)
        number.setObjectName("metric_value")
        detail = QLabel(note)
        detail.setObjectName("muted")
        detail.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(number)
        layout.addWidget(detail)
        return card

    def add_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        title = QLabel("Resumen general")
        title.setObjectName("page_title")
        description = QLabel(
            "Una vista rápida de la actividad del negocio."
        )
        description.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(description)

        cards = QHBoxLayout()
        cards.setSpacing(14)
        cards.addWidget(self.make_card(
            "VENTAS DEL DÍA", "$ 36.000", "Importe ilustrativo"
        ))
        cards.addWidget(self.make_card(
            "SALDOS PENDIENTES", "$ 36.500", "Ejemplo ficticio"
        ))
        cards.addWidget(self.make_card(
            "CLIENTES", "3", "Registros de demostración"
        ))
        cards.addWidget(self.make_card(
            "PRODUCTOS", "4", "Artículos de ejemplo"
        ))
        layout.addLayout(cards)

        actions_frame = QFrame()
        actions_frame.setObjectName("card")
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(20, 18, 20, 18)
        actions_layout.setSpacing(12)

        actions_title = QLabel("Accesos rápidos")
        actions_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        actions_layout.addWidget(actions_title)

        actions_row = QHBoxLayout()
        for label, target in [
            ("Consultar productos", "Productos"),
            ("Buscar clientes", "Clientes"),
            ("Ver ventas", "Ventas"),
            ("Consultar deudas", "Cuentas corrientes"),
        ]:
            button = QPushButton(label)
            button.setObjectName("primary")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, page_name=target:
                self.navigate(page_name)
            )
            actions_row.addWidget(button)

        actions_layout.addLayout(actions_row)
        layout.addWidget(actions_frame)

        recent_title = QLabel("Actividad de ejemplo")
        recent_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(recent_title)

        table = QTableWidget(3, 4)
        table.setHorizontalHeaderLabels(
            ["Movimiento", "Referencia", "Importe", "Tipo de dato"]
        )
        rows = [
            ["Venta de mostrador", "DEMO-002", "$ 12.000", "Ficticio"],
            ["Venta en cuenta", "DEMO-001", "$ 24.000", "Ficticio"],
            ["Saldo de cliente", "Cliente demo 2", "$ 12.500", "Ficticio"],
        ]
        self.fill_table(table, rows)
        layout.addWidget(table, 1)

        notice = QLabel(
            "Importante: todos los importes y registros visibles son ficticios."
        )
        notice.setObjectName("muted")
        layout.addWidget(notice)

        self.pages.addWidget(page)

    def add_products_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(17)

        title = QLabel("Productos")
        title.setObjectName("page_title")
        subtitle = QLabel("Catálogo, variantes y disponibilidad de mercadería.")
        subtitle.setObjectName("muted")

        search = QLineEdit()
        search.setPlaceholderText("Buscar productos...")
        search.setClearButtonEnabled(True)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["Producto", "Categoría", "Precio", "Variantes", "Stock total"]
        )

        buttons_row = QHBoxLayout()
        new_button = QPushButton("Nuevo producto")
        new_button.setObjectName("primary")
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_button = QPushButton("Editar")
        edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        variants_button = QPushButton("Agregar variante")
        variants_button.setCursor(Qt.CursorShape.PointingHandCursor)
        stock_button = QPushButton("Ajustar stock")
        stock_button.setCursor(Qt.CursorShape.PointingHandCursor)
        deactivate_button = QPushButton("Desactivar")
        deactivate_button.setCursor(Qt.CursorShape.PointingHandCursor)

        buttons_row.addWidget(new_button)
        buttons_row.addWidget(edit_button)
        buttons_row.addWidget(variants_button)
        buttons_row.addWidget(stock_button)
        buttons_row.addWidget(deactivate_button)
        buttons_row.addStretch()

        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_row)

        def refresh_products():
            table.setRowCount(0)
            table.setSortingEnabled(False)

            try:
                products = listar_productos(search.text())
            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudieron cargar los productos:\n{error}",
                )
                products = []

            for product in products:
                row = table.rowCount()
                table.insertRow(row)
                values = [
                    product["nombre"],
                    product["categoria"],
                    f"$ {product['precio_centavos'] / 100:,.2f}",
                    str(product["cantidad_variantes"]),
                    str(product["stock_total"]),
                ]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setFlags(
                        item.flags() & ~Qt.ItemFlag.ItemIsEditable
                    )
                    if column == 0:
                        item.setData(
                            Qt.ItemDataRole.UserRole,
                            product["id"],
                        )
                    if column in (2, 3, 4):
                        item.setTextAlignment(
                            Qt.AlignmentFlag.AlignRight
                            | Qt.AlignmentFlag.AlignVCenter
                        )
                    table.setItem(row, column, item)
            table.setSortingEnabled(True)
            table.resizeColumnsToContents()
            table.horizontalHeader().setStretchLastSection(True)

        def product_form(product=None):
            dialog = QDialog(self)
            dialog.setWindowTitle(
                "Editar producto" if product else "Nuevo producto"
            )
            dialog.setMinimumWidth(390)
            form = QFormLayout(dialog)
            name_input = QLineEdit(
                product["nombre"] if product else ""
            )
            category_input = QLineEdit(
                product["categoria"] if product else ""
            )
            price_input = QDoubleSpinBox()
            price_input.setRange(0, 999999999)
            price_input.setDecimals(2)
            price_input.setPrefix("$ ")
            price_input.setSingleStep(500)
            if product:
                price_input.setValue(
                    product["precio_centavos"] / 100
                )
            form.addRow("Nombre:", name_input)
            form.addRow("Categoría:", category_input)
            form.addRow("Precio:", price_input)

            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            form.addRow(buttons)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                nombre = name_input.text()
                categoria = category_input.text()
                precio = int(price_input.value() * 100)

                try:
                    if product:
                        motivo, ok = QInputDialog.getText(
                            self,
                            "Motivo de modificación",
                            "Describe el motivo de esta modificación:",
                        )
                        if not ok or not motivo.strip():
                            QMessageBox.warning(
                                self,
                                "Cancelado",
                                "Se requiere un motivo para modificar el producto.",
                            )
                            return
                        editar_producto(
                            product["id"],
                            nombre,
                            categoria,
                            precio,
                            motivo,
                        )
                    else:
                        crear_producto(nombre, categoria, precio)
                    refresh_products()
                except Exception as error:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"No se pudo guardar el producto:\n{error}",
                    )

        def variant_form(product_id):
            dialog = QDialog(self)
            dialog.setWindowTitle("Nueva variante")
            dialog.setMinimumWidth(320)
            form = QFormLayout(dialog)
            talle_input = QLineEdit()
            color_input = QLineEdit()
            stock_input = QSpinBox()
            stock_input.setRange(0, 99999)
            stock_input.setValue(0)

            form.addRow("Talle:", talle_input)
            form.addRow("Color:", color_input)
            form.addRow("Stock inicial:", stock_input)

            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            form.addRow(buttons)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                try:
                    crear_variante(
                        producto_id=product_id,
                        talle=talle_input.text(),
                        color=color_input.text(),
                        stock_inicial=stock_input.value(),
                        motivo="Alta desde interfaz",
                    )
                    refresh_products()
                except Exception as error:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"No se pudo crear la variante:\n{error}",
                    )

        def selected_product_id():
            selected = table.selectedItems()
            if not selected:
                QMessageBox.warning(
                    self,
                    "Selección requerida",
                    "Selecciona un producto primero.",
                )
                return None
            return selected[0].data(Qt.ItemDataRole.UserRole)

        def create_product():
            product_form()

        def edit_selected_product():
            product_id = selected_product_id()
            if product_id is None:
                return
            try:
                from app.services.productos_service import obtener_producto
                product = obtener_producto(product_id)
                if product:
                    product_form(dict(product))
            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo cargar el producto:\n{error}",
                )

        def manage_variants():
            product_id = selected_product_id()
            if product_id is None:
                return
            variant_form(product_id)

        def adjust_stock():
            product_id = selected_product_id()
            if product_id is None:
                return
            try:
                variants = listar_variantes(product_id)
            except Exception as error:
                QMessageBox.critical(
                    self, "Error", str(error)
                )
                return
            if not variants:
                QMessageBox.information(
                    self,
                    "Sin variantes",
                    "Este producto no tiene variantes activas. "
                    "Primero agregá un talle y color.",
                )
                return
            options = [
                (
                    f"ID {v['id']} | "
                    f"Talle: {v['talle'] or '—'} | "
                    f"Color: {v['color'] or '—'} | "
                    f"Stock: {v['stock_actual']}"
                )
                for v in variants
            ]
            selected, ok = QInputDialog.getItem(
                self,
                "Ajustar stock",
                "Seleccioná la variante a ajustar:",
                options,
                editable=False,
            )
            if not ok or not selected:
                return
            variant_index = options.index(selected)
            variant = variants[variant_index]
            variante_id = variant["id"]
            cambio, ok = QInputDialog.getInt(
                self,
                "Ajustar stock",
                f"Variante: {selected}\n\n"
                "Ingresá el cambio de stock (positivo para sumar, negativo para restar):",
                0,
                -99999,
                99999,
                1,
            )
            if not ok:
                return
            if cambio == 0:
                QMessageBox.warning(
                    self,
                    "Valor inválido",
                    "El cambio no puede ser cero.",
                )
                return
            motivo, ok = QInputDialog.getText(
                self,
                "Motivo del ajuste",
                "Describe el motivo de este ajuste de stock:",
            )
            if not ok or not motivo.strip():
                QMessageBox.warning(
                    self,
                    "Cancelado",
                    "Se requiere un motivo para ajustar el stock.",
                )
                return
            try:
                nuevo_stock = ajustar_stock(
                    variante_id=variante_id,
                    cambio=cambio,
                    motivo=motivo,
                )
                QMessageBox.information(
                    self,
                    "Stock ajustado",
                    f"Stock actualizado: {nuevo_stock}",
                )
                refresh_products()
            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se pudo ajustar el stock:\n{error}",
                )

        def deactivate_selected_product():
            product_id = selected_product_id()
            if product_id is None:
                return
            selected = table.selectedItems()
            product_name = selected[0].text()

            reply = QMessageBox.question(
                self,
                "Confirmar desactivación",
                f"¿Desactivar el producto '{product_name}'?\n\n"
                "Esta acción no elimina el historial, pero oculta el producto.",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                motivo, ok = QInputDialog.getText(
                    self,
                    "Motivo de desactivación",
                    "Describe el motivo de esta desactivación:",
                )
                if ok and motivo.strip():
                    try:
                        desactivar_producto(product_id, motivo)
                        refresh_products()
                    except Exception as error:
                        QMessageBox.critical(
                            self,
                            "Error",
                            f"No se pudo desactivar el producto:\n{error}",
                        )

        def handle_edit(item):
            if item.column() == 0:
                edit_selected_product()

        new_button.clicked.connect(create_product)
        edit_button.clicked.connect(edit_selected_product)
        variants_button.clicked.connect(manage_variants)
        stock_button.clicked.connect(adjust_stock)
        deactivate_button.clicked.connect(deactivate_selected_product)
        table.itemDoubleClicked.connect(handle_edit)
        search.textChanged.connect(refresh_products)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(search)
        layout.addWidget(buttons_widget)
        layout.addWidget(table, 1)

        self.pages.addWidget(page)
        refresh_products()

    def add_table_page(self, title_text, description, headers, rows):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(17)

        title = QLabel(title_text)
        title.setObjectName("page_title")
        subtitle = QLabel(description)
        subtitle.setObjectName("muted")

        search = QLineEdit()
        search.setPlaceholderText(f"Buscar en {title_text.lower()}...")
        search.setClearButtonEnabled(True)

        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        self.fill_table(table, rows)
        table.setSortingEnabled(True)

        def filter_rows(text):
            for row in range(table.rowCount()):
                matches = any(
                    text.casefold() in (
                        table.item(row, col).text().casefold()
                        if table.item(row, col) else ""
                    )
                    for col in range(table.columnCount())
                )
                table.setRowHidden(row, not matches)

        search.textChanged.connect(filter_rows)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(search)
        layout.addWidget(table, 1)

        self.pages.addWidget(page)

    @staticmethod
    def fill_table(table, rows):
        table.setRowCount(len(rows))
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(42)

        for row_index, values in enumerate(rows):
            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(
                    item.flags() & ~Qt.ItemFlag.ItemIsEditable
                )
                table.setItem(row_index, col_index, item)

        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def navigate(self, page_name):
        index_by_name = {
            "Inicio": 0,
            "Productos": 1,
            "Clientes": 2,
            "Ventas": 3,
            "Cuentas corrientes": 4,
            "Reportes y comprobantes": 5,
        }

        self.pages.setCurrentIndex(index_by_name[page_name])

        for name, button in self.nav_buttons.items():
            button.setProperty("active", name == page_name)
            button.style().unpolish(button)
            button.style().polish(button)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    try:
        initialize_database()
    except Exception as error:
        QMessageBox.critical(
            None,
            "Error de base de datos",
            f"No se pudo inicializar la base de datos:\n{error}",
        )
        return 1
    window = MainWindow()
    window.show()
    print("SoftTech iniciado correctamente.", flush=True)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
