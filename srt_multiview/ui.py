import sys
import time

from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

import qdarktheme

from . import core
from .paths import APP_ICON_ICO_PATH, APP_ICON_PNG_PATH

APP_ID = "srtmultiview.desktop"

APP_STYLESHEET = """
QWidget {
    background: #0b1120;
    color: #e2e8f0;
    font-size: 12px;
}
QLabel#Title {
    font-size: 24px;
    font-weight: 600;
    color: #f8fafc;
}
QLabel#Subtitle {
    color: #94a3b8;
}
QLabel#StatusChip {
    background: #1e293b;
    color: #e2e8f0;
    padding: 4px 12px;
    border-radius: 10px;
}
QFrame#Card, QGroupBox {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #cbd5f5;
}
QPushButton {
    background: #1f2937;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 12px;
}
QPushButton:hover {
    background: #263247;
}
QPushButton#PrimaryButton {
    background: #2563eb;
    border-color: #1d4ed8;
}
QPushButton#PrimaryButton:hover {
    background: #3b82f6;
}
QPushButton#SuccessButton {
    background: #16a34a;
    border-color: #15803d;
}
QPushButton#SuccessButton:hover {
    background: #22c55e;
}
QPushButton#DangerButton {
    background: #dc2626;
    border-color: #b91c1c;
}
QPushButton#DangerButton:hover {
    background: #ef4444;
}
QLineEdit, QSpinBox, QComboBox {
    background: #0b1220;
    border: 1px solid #1f2937;
    border-radius: 6px;
    padding: 4px 6px;
}
QTableWidget {
    background: #0b1220;
    border: 1px solid #1f2937;
    border-radius: 10px;
    gridline-color: #1f2937;
    alternate-background-color: #0f172a;
}
QHeaderView::section {
    background: #111827;
    padding: 6px;
    border: 0px;
    color: #94a3b8;
}
QTableWidget::item {
    padding: 6px;
}
QTableWidget::item:selected {
    background: #1f2937;
}
QListWidget {
    background: #0b1220;
    border: 1px solid #1f2937;
    border-radius: 10px;
}
QListWidget::item {
    padding: 6px;
}
QListWidget::item:selected {
    background: #1f2937;
}
QSplitter::handle {
    background: #1f2937;
}
"""

DRACULA_OVERLAY_QSS = """
QLabel#Title {
    font-size: 24px;
    font-weight: 600;
    color: #f8f8f2;
}
QLabel#Subtitle {
    color: #bfbfbf;
}
QLabel#StatusChip {
    background: #44475a;
    color: #f8f8f2;
    padding: 4px 12px;
    border-radius: 10px;
}
QFrame#Card, QGroupBox {
    background: #21222c;
    border: 1px solid #44475a;
    border-radius: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #bd93f9;
}
QPushButton#PrimaryButton {
    background: #bd93f9;
    border-color: #bd93f9;
    color: #282a36;
}
QPushButton#PrimaryButton:hover {
    background: #caa9fa;
}
QPushButton#SuccessButton {
    background: #50fa7b;
    border-color: #50fa7b;
    color: #282a36;
}
QPushButton#SuccessButton:hover {
    background: #6bff91;
}
QPushButton#DangerButton {
    background: #ff5555;
    border-color: #ff5555;
    color: #282a36;
}
QPushButton#DangerButton:hover {
    background: #ff6e6e;
}

QLabel#GlobalStateRunning {
    background: #14532d;
    color: #dcfce7;
    padding: 4px 12px;
    border-radius: 10px;
}

QLabel#GlobalStateStopped {
    background: #7f1d1d;
    color: #fee2e2;
    padding: 4px 12px;
    border-radius: 10px;
}

QLineEdit, QSpinBox, QComboBox {
    padding: 4px 6px;
    min-height: 28px;
    max-height: 28px;
}

QComboBox::drop-down {
    border: 0px;
}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setFont(QFont("Bahnschrift", 10))
    qdarktheme.setup_theme(
        theme="dark",
        corner_shape="rounded",
        custom_colors={"primary": "#bd93f9"},
        additional_qss=DRACULA_OVERLAY_QSS,
    )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRT Multiview")
        if APP_ICON_ICO_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_ICO_PATH)))
        elif APP_ICON_PNG_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG_PATH)))
        self.resize(1000, 650)
        self.setMinimumSize(900, 600)

        self.config = core.load_config()
        self.displays = []
        self.is_running = False

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        header_card = QFrame()
        header_card.setObjectName("Card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(16)

        title = QLabel("SRT Multiview")
        title.setObjectName("Title")
        subtitle = QLabel("Routing SRT vers écrans Windows")
        subtitle.setObjectName("Subtitle")

        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        self.streams_chip = QLabel("Flux: 0")
        self.streams_chip.setObjectName("StatusChip")
        self.displays_chip = QLabel("Écrans: 0")
        self.displays_chip.setObjectName("StatusChip")
        self.status_chip = QLabel("Actifs: 0/0")
        self.status_chip.setObjectName("StatusChip")
        self.global_state_chip = QLabel("ARRÊTÉ")
        self.global_state_chip.setObjectName("StatusChip")
        chip_row.addWidget(self.streams_chip)
        chip_row.addWidget(self.displays_chip)
        chip_row.addWidget(self.status_chip)
        chip_row.addWidget(self.global_state_chip)
        chip_row.addStretch()

        title_layout = QVBoxLayout()
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.addLayout(chip_row)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.btn_toggle = QPushButton("Démarrer")
        self.btn_toggle.setObjectName("SuccessButton")
        self.btn_toggle.clicked.connect(self.toggle_start_stop)
        self.btn_toggle.setMinimumWidth(160)
        self.btn_toggle.setMinimumHeight(38)
        actions_layout.addWidget(self.btn_toggle)

        header_layout.addLayout(title_layout, stretch=1)
        header_layout.addLayout(actions_layout)

        layout.addWidget(header_card)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(0)
        layout.addWidget(splitter, stretch=1)

        left_panel = QFrame()
        left_panel.setObjectName("Card")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        displays_group = QGroupBox("Écrans détectés")
        displays_layout = QVBoxLayout(displays_group)
        self.displays_list = QListWidget()
        self.displays_list.setSpacing(4)
        self.displays_list.setSelectionMode(QAbstractItemView.NoSelection)
        displays_layout.addWidget(self.displays_list)

        prefs_group = QGroupBox("Préférences")
        prefs_layout = QVBoxLayout(prefs_group)
        self.exclude_primary = QCheckBox("Exclure l'écran principal")
        self.exclude_primary.setChecked(bool(self.config.get("excludePrimaryDisplay", True)))
        self.exclude_primary.stateChanged.connect(self.on_exclude_primary_changed)
        prefs_layout.addWidget(self.exclude_primary)
        prefs_note = QLabel('Astuce : utilisez "Rafraîchir" après un changement d\'écran.')
        prefs_note.setObjectName("Subtitle")
        prefs_note.setWordWrap(True)
        prefs_layout.addWidget(prefs_note)

        left_layout.addWidget(displays_group)
        left_layout.addWidget(prefs_group)
        left_layout.addStretch()

        streams_panel = QFrame()
        streams_panel.setObjectName("Card")
        streams_layout = QVBoxLayout(streams_panel)
        streams_layout.setContentsMargins(16, 16, 16, 16)
        streams_layout.setSpacing(12)

        streams_header = QHBoxLayout()
        streams_title = QLabel("Flux SRT")
        streams_title_font = QFont("Bahnschrift", 13)
        streams_title_font.setWeight(QFont.Medium)
        streams_title.setFont(streams_title_font)

        self.btn_add = QPushButton("Ajouter un flux")
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_add.clicked.connect(self.add_stream)

        self.btn_remove = QPushButton("Supprimer")
        self.btn_remove.setObjectName("DangerButton")
        self.btn_remove.clicked.connect(self.remove_selected_stream)

        streams_header.addWidget(streams_title)
        streams_header.addStretch(1)
        streams_header.addWidget(self.btn_add)
        streams_header.addWidget(self.btn_remove)

        self.table = QTableWidget(0, 5)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setHorizontalHeaderLabels(["Nom", "Port", "Latence (ms)", "Écran", "Statut"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(52)
        header = self.table.horizontalHeader()
        header.setSectionsMovable(False)
        header.setSectionsClickable(False)
        header.setHighlightSections(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setStretchLastSection(False)
        header.resizeSection(1, 70)
        header.resizeSection(2, 110)
        header.resizeSection(4, 110)

        streams_layout.addLayout(streams_header)
        streams_layout.addWidget(self.table)

        splitter.addWidget(left_panel)
        splitter.addWidget(streams_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        left_panel.setMinimumWidth(300)
        left_panel.setMaximumWidth(300)
        streams_panel.setMinimumWidth(480)
        splitter.setSizes([300, 700])

        self.refresh_displays()
        self.reload_table()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(1000)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.save)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            row = obj.property("table_row")
            if isinstance(row, int) and row >= 0:
                self.table.selectRow(row)
        return super().eventFilter(obj, event)

    def on_exclude_primary_changed(self):
        self.config["excludePrimaryDisplay"] = bool(self.exclude_primary.isChecked())
        self.schedule_save()
        self.refresh_displays()
        self.reload_table()

    def refresh_displays(self):
        exclude = bool(self.config.get("excludePrimaryDisplay", True))
        self.displays = core.get_displays(exclude_primary=exclude)
        self.render_displays()
        self.update_header_chips()

    def reload_table(self):
        self.config = core.normalize_config(self.config)
        streams = self.config.get("streams", [])

        display_ids = {str(d["id"]) for d in self.displays}

        self.table.setRowCount(len(streams))

        for row, stream in enumerate(streams):
            self.table.setRowHeight(row, 58)

            def wrap_widget(widget: QWidget) -> QWidget:
                container = QWidget()
                layout = QVBoxLayout(container)
                layout.setContentsMargins(0, 6, 0, 6)
                layout.setAlignment(Qt.AlignVCenter)
                layout.addWidget(widget)
                return container

            name_edit = QLineEdit(str(stream.get("name", "")))
            name_edit.setFixedHeight(28)
            name_edit.setProperty("table_row", row)
            name_edit.installEventFilter(self)
            name_edit.editingFinished.connect(self.make_stream_updater(row))
            self.table.setCellWidget(row, 0, wrap_widget(name_edit))

            port_spin = QSpinBox()
            port_spin.setRange(1, 65535)
            port_spin.setValue(int(stream.get("port", 9000)))
            port_spin.setButtonSymbols(QSpinBox.NoButtons)
            port_spin.setFixedHeight(28)
            port_spin.setProperty("table_row", row)
            port_spin.installEventFilter(self)
            port_spin.valueChanged.connect(self.make_stream_updater(row))
            self.table.setCellWidget(row, 1, wrap_widget(port_spin))

            latency_spin = QSpinBox()
            latency_spin.setRange(0, 5000)
            latency_spin.setValue(int(stream.get("latency", 120)))
            latency_spin.setButtonSymbols(QSpinBox.NoButtons)
            latency_spin.setFixedHeight(28)
            latency_spin.setProperty("table_row", row)
            latency_spin.installEventFilter(self)
            latency_spin.valueChanged.connect(self.make_stream_updater(row))
            self.table.setCellWidget(row, 2, wrap_widget(latency_spin))

            display_combo = QComboBox()
            display_combo.addItem("— Non assigné —", "")
            for d in self.displays:
                display_combo.addItem(d["name"], str(d["id"]))
            display_combo.setMinimumWidth(140)
            display_combo.setFixedHeight(28)
            display_combo.setProperty("table_row", row)
            display_combo.installEventFilter(self)

            stream_id = str(stream.get("id"))
            current_display_id = self.config.get("mapping", {}).get(stream_id)
            if current_display_id is not None and str(current_display_id) in display_ids:
                idx = display_combo.findData(str(current_display_id))
                if idx >= 0:
                    display_combo.setCurrentIndex(idx)
            elif current_display_id is not None:
                self.config.get("mapping", {}).pop(stream_id, None)

            display_combo.currentIndexChanged.connect(self.make_stream_updater(row))
            self.table.setCellWidget(row, 3, wrap_widget(display_combo))

            status_label = QLabel("⏹ arrêté")
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet("color: #f87171;")
            self.table.setCellWidget(row, 4, wrap_widget(status_label))

        self.refresh_status()

    def make_stream_updater(self, row: int):
        def _update(*_args):
            self.update_config_from_row(row)
            self.schedule_save()

        return _update

    def schedule_save(self):
        self.autosave_timer.start(500)

    def update_config_from_row(self, row: int):
        streams = self.config.get("streams", [])
        if row < 0 or row >= len(streams):
            return

        stream = streams[row]
        stream_id = str(stream.get("id"))

        def unwrap(col: int):
            container = self.table.cellWidget(row, col)
            if container and container.layout() and container.layout().count():
                return container.layout().itemAt(0).widget()
            return None

        name_edit = unwrap(0)
        port_spin = unwrap(1)
        latency_spin = unwrap(2)
        display_combo = unwrap(3)

        if name_edit:
            stream["name"] = name_edit.text().strip() or stream_id
        if port_spin:
            stream["port"] = int(port_spin.value())
        if latency_spin:
            stream["latency"] = int(latency_spin.value())

        display_id = display_combo.currentData() if display_combo else ""
        mapping = self.config.setdefault("mapping", {})
        if display_id:
            mapping[stream_id] = str(display_id)
        else:
            mapping.pop(stream_id, None)

    def save(self):
        for row in range(self.table.rowCount()):
            self.update_config_from_row(row)

        self.config = core.normalize_config(self.config)
        core.save_config(self.config)

    def check_duplicate_ports(self) -> list[int]:
        streams = self.config.get("streams", [])
        ports = [s.get("port") for s in streams]
        seen = set()
        duplicates = set()
        for p in ports:
            if p in seen:
                duplicates.add(p)
            seen.add(p)
        return list(duplicates)

    def start_all(self):
        self.save()

        duplicate_ports = self.check_duplicate_ports()
        if duplicate_ports:
            QMessageBox.warning(
                self,
                "Ports en double",
                "Attention : les ports suivants sont utilisés plusieurs fois :\n"
                + ", ".join(map(str, duplicate_ports))
                + "\n\nCela peut causer des conflits.",
            )

        results = core.apply_mapping(self.config)
        failures = [sid for sid, ok in results.items() if not ok]
        self.refresh_status()

        if failures:
            QMessageBox.warning(
                self,
                "Démarrage partiel",
                "Certains flux n'ont pas démarré (pas d'écran assigné, ou ffplay manquant).\n\n"
                + "\n".join(failures),
            )
        self.update_toggle_button(True)

    def stop_all(self):
        core.player_manager.stop_all()
        self.refresh_status()
        self.update_toggle_button(False)

    def toggle_start_stop(self):
        if self.is_running:
            self.stop_all()
        else:
            self.start_all()

    def update_toggle_button(self, is_running: bool):
        self.is_running = is_running
        if is_running:
            self.btn_toggle.setText("Arrêter")
            self.btn_toggle.setObjectName("DangerButton")
        else:
            self.btn_toggle.setText("Démarrer")
            self.btn_toggle.setObjectName("SuccessButton")
        self.btn_toggle.style().unpolish(self.btn_toggle)
        self.btn_toggle.style().polish(self.btn_toggle)

    def refresh_status(self):
        status = core.player_manager.status()
        streams = self.config.get("streams", [])

        for row, stream in enumerate(streams):
            stream_id = str(stream.get("id"))
            running = status.get(stream_id, False)
            container = self.table.cellWidget(row, 4)
            if container and container.layout() and container.layout().count():
                label = container.layout().itemAt(0).widget()
                if isinstance(label, QLabel):
                    label.setText("▶ en cours" if running else "⏹ arrêté")
                    label.setStyleSheet("color: #22c55e;" if running else "color: #f87171;")

        self.update_header_chips(status)
        self.update_toggle_button(any(status.values()))

    def add_stream(self):
        now = int(time.time() * 1000)
        next_index = len(self.config.get("streams", [])) + 1
        stream_id = f"stream-{now}"
        self.config.setdefault("streams", []).append(
            {"id": stream_id, "name": f"Flux {next_index}", "port": 9000 + next_index, "latency": 120}
        )
        self.reload_table()
        self.schedule_save()

    def remove_selected_stream(self):
        row = self.table.currentRow()
        streams = self.config.get("streams", [])
        if row < 0 or row >= len(streams):
            return

        stream = streams[row]
        stream_id = str(stream.get("id"))
        stream_name = stream.get("name", stream_id)
        reply = QMessageBox.question(
            self,
            "Suppression",
            f"Supprimer le flux « {stream_name} » ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        core.player_manager.stop_player(stream_id)
        streams.pop(row)
        self.config.get("mapping", {}).pop(stream_id, None)
        self.reload_table()
        self.schedule_save()

    def render_displays(self):
        self.displays_list.clear()
        if not self.displays:
            empty_item = QListWidgetItem("Aucun écran détecté")
            empty_item.setForeground(QColor("#94a3b8"))
            self.displays_list.addItem(empty_item)
            return

        for display in self.displays:
            label = f"{display['name']} — {display['width']}x{display['height']}"
            if display.get("isPrimary"):
                label += " (Principal)"
            item = QListWidgetItem(label)
            color = QColor("#60a5fa") if display.get("isPrimary") else QColor("#e2e8f0")
            item.setForeground(color)
            item.setToolTip(f"ID: {display['id']} | Position: {display['x']}, {display['y']}")
            self.displays_list.addItem(item)

    def update_header_chips(self, status: dict | None = None):
        stream_count = len(self.config.get("streams", []))
        display_count = len(self.displays)
        if status is None:
            status = core.player_manager.status()
        active_count = sum(1 for value in status.values() if value)

        self.streams_chip.setText(f"Flux: {stream_count}")
        self.displays_chip.setText(f"Écrans: {display_count}")
        self.status_chip.setText(f"Actifs: {active_count}/{stream_count}")
        if active_count > 0:
            self.global_state_chip.setText("EN COURS")
            self.global_state_chip.setObjectName("GlobalStateRunning")
        else:
            self.global_state_chip.setText("ARRÊTÉ")
            self.global_state_chip.setObjectName("GlobalStateStopped")
        self.global_state_chip.style().unpolish(self.global_state_chip)
        self.global_state_chip.style().polish(self.global_state_chip)

    def closeEvent(self, event):
        core.player_manager.stop_all()
        event.accept()


def main() -> None:
    qdarktheme.enable_hi_dpi()

    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:
            pass

    app = QApplication(sys.argv)
    if APP_ICON_ICO_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_ICO_PATH)))
    elif APP_ICON_PNG_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PNG_PATH)))

    apply_theme(app)
    w = MainWindow()
    w.show()
    raise SystemExit(app.exec())
