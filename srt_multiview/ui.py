import sys
import time
import uuid

from PySide6.QtCore import QObject, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QInputDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from . import core
from .paths import APP_ICON_ICO_PATH, APP_ICON_PNG_PATH, CONFIG_PATH
from .styles import apply_theme, enable_hi_dpi

APP_ID = "srtmultiview.desktop"



class RoutingDialog(QDialog):
    def __init__(self, parent: "MainWindow"):
        super().__init__(parent)
        self.main = parent
        self.setWindowTitle("Routage SRT → UDP multicast")
        self.setMinimumSize(760, 460)

        root = QFrame()
        root.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(root)

        outer = QHBoxLayout(root)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        left = QVBoxLayout()
        left.setSpacing(8)
        self.routes_list = QListWidget()
        self.routes_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.routes_list.currentRowChanged.connect(self.on_select_route)
        self.routes_list.setMinimumWidth(260)
        left.addWidget(self.routes_list, stretch=1)

        left_btns = QHBoxLayout()
        left_btns.setSpacing(8)
        self.btn_add = QPushButton("+ Ajouter")
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_add.setMinimumHeight(34)
        self.btn_add.clicked.connect(self.add_route)
        left_btns.addWidget(self.btn_add)
        self.btn_delete = QPushButton("Supprimer")
        self.btn_delete.setObjectName("DangerButton")
        self.btn_delete.setMinimumHeight(34)
        self.btn_delete.clicked.connect(self.delete_route)
        left_btns.addWidget(self.btn_delete)
        left.addLayout(left_btns)

        right = QVBoxLayout()
        right.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setFixedHeight(28)
        self.input_port_spin = QSpinBox()
        self.input_port_spin.setRange(1, 65535)
        self.input_port_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.input_port_spin.setFixedHeight(28)
        self.input_latency_spin = QSpinBox()
        self.input_latency_spin.setRange(0, 5000)
        self.input_latency_spin.setSuffix(" ms")
        self.input_latency_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.input_latency_spin.setFixedHeight(28)

        self.maddr_edit = QLineEdit()
        self.maddr_edit.setPlaceholderText("ex: 239.10.10.10")
        self.maddr_edit.setFixedHeight(28)
        self.mport_spin = QSpinBox()
        self.mport_spin.setRange(1, 65535)
        self.mport_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.mport_spin.setFixedHeight(28)
        self.ttl_spin = QSpinBox()
        self.ttl_spin.setRange(1, 255)
        self.ttl_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.ttl_spin.setFixedHeight(28)
        self.pkt_spin = QSpinBox()
        self.pkt_spin.setRange(188, 9000)
        self.pkt_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.pkt_spin.setFixedHeight(28)

        def _row_widget(label: str, widget: QWidget) -> QWidget:
            row_w = QWidget()
            row = QHBoxLayout(row_w)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)
            lbl = QLabel(label)
            lbl.setObjectName("FormLabel")
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setFixedWidth(110)
            row.addWidget(lbl)
            row.addWidget(widget, stretch=1)
            return row_w

        right.addWidget(_row_widget("Nom", self.name_edit))
        right.addWidget(_row_widget("SRT in port", self.input_port_spin))
        right.addWidget(_row_widget("SRT latence", self.input_latency_spin))

        self.advanced_chk = QCheckBox("Options avancées")
        self.advanced_chk.setMinimumHeight(24)
        right.addWidget(self.advanced_chk)

        self._adv_row_maddr = _row_widget("Multicast IP", self.maddr_edit)
        self._adv_row_mport = _row_widget("Multicast port", self.mport_spin)
        self._adv_row_ttl = _row_widget("TTL", self.ttl_spin)
        self._adv_row_pkt = _row_widget("pkt_size", self.pkt_spin)
        right.addWidget(self._adv_row_maddr)
        right.addWidget(self._adv_row_mport)
        right.addWidget(self._adv_row_ttl)
        right.addWidget(self._adv_row_pkt)

        def _set_advanced_visible(visible: bool):
            self._adv_row_maddr.setVisible(visible)
            self._adv_row_mport.setVisible(visible)
            self._adv_row_ttl.setVisible(visible)
            self._adv_row_pkt.setVisible(visible)

        self.advanced_chk.toggled.connect(_set_advanced_visible)
        self.advanced_chk.setChecked(False)
        _set_advanced_visible(False)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Subtitle")
        self.status_label.setWordWrap(True)
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.status_label.setMinimumHeight(34)
        right.addWidget(self.status_label)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.btn_toggle = QPushButton("▶ Démarrer")
        self.btn_toggle.setObjectName("SuccessButton")
        self.btn_toggle.setMinimumHeight(36)
        self.btn_toggle.clicked.connect(self.toggle_route)
        actions.addWidget(self.btn_toggle)
        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.setMinimumHeight(36)
        self.btn_save.clicked.connect(self.save_route)
        actions.addWidget(self.btn_save)
        self.btn_close = QPushButton("Fermer")
        self.btn_close.setMinimumHeight(36)
        self.btn_close.clicked.connect(self.accept)
        actions.addWidget(self.btn_close)
        actions.addStretch(1)
        right.addLayout(actions)

        outer.addLayout(left, stretch=0)
        outer.addLayout(right, stretch=1)

        self.refresh_routes()

    def _routes(self) -> list[dict]:
        return list(self.main.config.get("routes", []) or [])

    def _selected_route_id(self) -> str:
        item = self.routes_list.currentItem()
        if not item:
            return ""
        return str(item.data(Qt.UserRole) or "")

    def refresh_routes(self):
        self.routes_list.blockSignals(True)
        try:
            self.routes_list.clear()
            status = core.route_manager.status()
            for r in self._routes():
                rid = str(r.get("id") or "")
                name = str(r.get("name") or rid)
                running = bool(status.get(rid, False))
                label = f"▶ {name}" if running else f"⏹ {name}"
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, rid)
                self.routes_list.addItem(item)
        finally:
            self.routes_list.blockSignals(False)

        if self.routes_list.count() > 0 and self.routes_list.currentRow() < 0:
            self.routes_list.setCurrentRow(0)
        self.on_select_route(self.routes_list.currentRow())

    def on_select_route(self, _row: int):
        rid = self._selected_route_id()
        route = next((r for r in self._routes() if str(r.get("id")) == rid), None)
        if not route:
            self.name_edit.setText(self.name_edit.text() or f"Route {self.routes_list.count() + 1}")
            self.input_port_spin.setValue(int(self.input_port_spin.value() or 9001))
            self.input_latency_spin.setValue(int(self.input_latency_spin.value() or 120))
            if not self.maddr_edit.text().strip():
                self.maddr_edit.setText("239.10.10.10")
            if int(self.mport_spin.value() or 0) <= 0:
                self.mport_spin.setValue(1234)
            if int(self.ttl_spin.value() or 0) <= 0:
                self.ttl_spin.setValue(1)
            if int(self.pkt_spin.value() or 0) <= 0:
                self.pkt_spin.setValue(1316)

            self.status_label.setText("Aucune route enregistrée. Renseigne les champs puis clique « Enregistrer ».")
            self.btn_toggle.setEnabled(True)
            self.btn_delete.setEnabled(False)
            self.btn_save.setEnabled(True)
            return

        self.btn_toggle.setEnabled(True)
        self.btn_delete.setEnabled(True)
        self.btn_save.setEnabled(True)

        self.name_edit.setText(str(route.get("name") or ""))
        self.input_port_spin.setValue(int(route.get("inputPort") or 9001))
        self.input_latency_spin.setValue(int(route.get("inputLatency") or 120))
        self.maddr_edit.setText(str(route.get("multicastAddr") or "239.10.10.10"))
        self.mport_spin.setValue(int(route.get("multicastPort") or 1234))
        self.ttl_spin.setValue(int(route.get("ttl") or 1))
        self.pkt_spin.setValue(int(route.get("pktSize") or 1316))

        running = bool(core.route_manager.status().get(rid, False))
        if running:
            self.btn_toggle.setText("⏹ Arrêter")
            self.btn_toggle.setObjectName("DangerButton")
            self.status_label.setText(
                f"En cours. Sortie : udp://@{self.maddr_edit.text().strip()}:{self.mport_spin.value()}"
            )
        else:
            self.btn_toggle.setText("▶ Démarrer")
            self.btn_toggle.setObjectName("SuccessButton")
            last = core.route_manager.last_error.get(rid)
            if last:
                self.status_label.setText("Arrêtée. Dernière erreur : " + str(last))
            else:
                self.status_label.setText("Arrêtée.")
        self.btn_toggle.style().unpolish(self.btn_toggle)
        self.btn_toggle.style().polish(self.btn_toggle)

    def add_route(self):
        rid = f"route-{uuid.uuid4().hex[:12]}"
        name, ok = QInputDialog.getText(self, "Nouvelle route", "Nom de la route :", text=f"Route {self.routes_list.count() + 1}")
        if not ok:
            return
        name = (name or "").strip() or rid

        existing_routes = self.main.config.get("routes") or []
        used_in_ports: set[int] = set()
        for r in existing_routes:
            if isinstance(r, dict):
                try:
                    used_in_ports.add(int(r.get("inputPort") or 0))
                except Exception:
                    pass
        for s in (self.main.config.get("streams") or []):
            if not isinstance(s, dict):
                continue
            if str(s.get("source") or "srt").strip().lower() != "srt":
                continue
            try:
                used_in_ports.add(int(s.get("port") or 0))
            except Exception:
                pass

        in_port = 9001
        while in_port in used_in_ports:
            in_port += 1

        used_mcast_ports: set[int] = set()
        for r in existing_routes:
            if isinstance(r, dict):
                try:
                    used_mcast_ports.add(int(r.get("multicastPort") or 0))
                except Exception:
                    pass
        mcast_port = 1234
        while mcast_port in used_mcast_ports:
            mcast_port += 1

        self.main.config.setdefault("routes", []).append(
            {
                "id": rid,
                "name": name,
                "inputPort": in_port,
                "inputLatency": 120,
                "multicastAddr": "239.10.10.10",
                "multicastPort": mcast_port,
                "pktSize": 1316,
                "ttl": 1,
            }
        )
        self.main.config = core.normalize_config(self.main.config)
        core.save_config(self.main.config)
        self.refresh_routes()
        for i in range(self.routes_list.count()):
            if str(self.routes_list.item(i).data(Qt.UserRole)) == rid:
                self.routes_list.setCurrentRow(i)
                break

    def delete_route(self):
        rid = self._selected_route_id()
        if not rid:
            return
        route = next((r for r in self._routes() if str(r.get("id")) == rid), None)
        name = str((route or {}).get("name") or rid)
        reply = QMessageBox.question(
            self,
            "Suppression",
            f"Supprimer la route « {name} » ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        core.route_manager.stop_route(rid)
        self.main.config["routes"] = [r for r in self._routes() if str(r.get("id")) != rid]
        for s in self.main.config.get("streams", []) or []:
            if str(s.get("source")) == "route" and str(s.get("sourceRouteId")) == rid:
                s["sourceRouteId"] = ""
                s["source"] = "srt"
        self.main.config = core.normalize_config(self.main.config)
        core.save_config(self.main.config)
        self.refresh_routes()

    def save_route(self):
        rid = self._selected_route_id()
        routes = self._routes()
        route = next((r for r in routes if str(r.get("id")) == rid), None) if rid else None

        if not route:
            rid = f"route-{uuid.uuid4().hex[:12]}"
            route = {"id": rid}
            routes.append(route)

        route["name"] = self.name_edit.text().strip() or rid
        route["inputPort"] = int(self.input_port_spin.value())
        route["inputLatency"] = int(self.input_latency_spin.value())
        route["multicastAddr"] = self.maddr_edit.text().strip() or "239.10.10.10"
        route["multicastPort"] = int(self.mport_spin.value())
        route["ttl"] = int(self.ttl_spin.value())
        route["pktSize"] = int(self.pkt_spin.value())
        self.main.config["routes"] = routes
        self.main.config = core.normalize_config(self.main.config)
        core.save_config(self.main.config)
        self.refresh_routes()

        for i in range(self.routes_list.count()):
            if str(self.routes_list.item(i).data(Qt.UserRole)) == rid:
                self.routes_list.setCurrentRow(i)
                break

    def toggle_route(self):
        rid = self._selected_route_id()
        if not rid:
            self.save_route()
            rid = self._selected_route_id()
            if not rid:
                return
        route = next((r for r in self._routes() if str(r.get("id")) == rid), None)
        if not route:
            return
        running = bool(core.route_manager.status().get(rid, False))
        if running:
            core.route_manager.stop_route(rid)
            self.refresh_routes()
            return
        self.save_route()
        route = next((r for r in self._routes() if str(r.get("id")) == rid), None)
        if not route:
            return
        result = core.route_manager.start_route(route)
        if not result.ok:
            QMessageBox.warning(self, "Routage", "Impossible de démarrer la route.\n\n" + (result.reason or "Erreur inconnue."))
        self.refresh_routes()


class _OMTDiscoveryWorker(QObject):
    finished = Signal(list, str)

    def __init__(self, timeout: float = 8.0):
        super().__init__()
        self._timeout = float(timeout)

    def run(self) -> None:
        sources, error = core.list_omt_sources(self._timeout)
        self.finished.emit(list(sources), error or "")


class OMTDiscoveryDialog(QDialog):
    """Modal source picker that runs ``ffmpeg -find_sources`` off the UI thread."""

    def __init__(self, parent: QWidget, current: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Découverte OMT")
        self.setMinimumSize(520, 360)
        self.selected_source: str = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.status_label = QLabel("Recherche en cours…")
        self.status_label.setObjectName("Subtitle")
        layout.addWidget(self.status_label)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(lambda _i: self._accept_selection())
        layout.addWidget(self.list_widget, stretch=1)

        manual_row = QHBoxLayout()
        manual_row.setSpacing(8)
        manual_lbl = QLabel("Source")
        manual_lbl.setObjectName("FormLabel")
        manual_lbl.setFixedWidth(60)
        manual_row.addWidget(manual_lbl)
        self.manual_edit = QLineEdit(current)
        self.manual_edit.setPlaceholderText("HOST (Source Name)")
        self.manual_edit.setFixedHeight(28)
        manual_row.addWidget(self.manual_edit, stretch=1)
        layout.addLayout(manual_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.refresh_btn = QPushButton("↻  Re-scanner")
        self.refresh_btn.clicked.connect(self._start_discovery)
        btn_row.addWidget(self.refresh_btn)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("Sélectionner")
        ok_btn.setObjectName("PrimaryButton")
        ok_btn.clicked.connect(self._accept_selection)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        self._thread: QThread | None = None
        self._worker: _OMTDiscoveryWorker | None = None

        QTimer.singleShot(0, self._start_discovery)

    def _start_discovery(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            return
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("Recherche en cours…")
        self.list_widget.clear()

        self._thread = QThread(self)
        self._worker = _OMTDiscoveryWorker(timeout=8.0)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_finished(self, sources: list, error: str) -> None:
        self.refresh_btn.setEnabled(True)
        self._thread = None
        self._worker = None
        self.list_widget.clear()
        if error:
            self.status_label.setText(f"⚠ {error}")
            return
        if not sources:
            self.status_label.setText("Aucune source OMT détectée sur le réseau.")
            return
        self.status_label.setText(f"{len(sources)} source(s) détectée(s).")
        for src in sources:
            QListWidgetItem(str(src), self.list_widget)
        self.list_widget.setCurrentRow(0)

    def _accept_selection(self) -> None:
        item = self.list_widget.currentItem()
        manual = self.manual_edit.text().strip()
        chosen = (item.text().strip() if item else "") or manual
        if not chosen:
            QMessageBox.warning(self, "Découverte OMT", "Sélectionne une source ou saisis-en une.")
            return
        self.selected_source = chosen
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRT Multiview")
        if APP_ICON_ICO_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_ICO_PATH)))
        elif APP_ICON_PNG_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG_PATH)))
        screen = QApplication.primaryScreen()
        available_h = 900
        if screen is not None:
            try:
                available_h = int(screen.availableGeometry().height())
            except Exception:
                available_h = 900

        target_h = min(max(860, int(available_h * 0.93)), 1080)
        self.resize(1260, target_h)
        self.setMinimumSize(1100, min(820, target_h))

        self.config = core.load_config()
        self.displays = []
        self.sender_displays = []
        self.is_running = False
        self.sender_is_running = False
        self.pending_stream_starts: dict[str, float] = {}
        self.global_start_until: float | None = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_status)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.save)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # ── Header ──
        header_card = QFrame()
        header_card.setObjectName("Card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(24, 18, 24, 18)
        header_layout.setSpacing(16)

        title = QLabel("SRT Multiview")
        title.setObjectName("Title")
        subtitle = QLabel("Routing SRT & émission OMT vers écrans Windows")
        subtitle.setObjectName("Subtitle")

        chip_row = QHBoxLayout()
        chip_row.setSpacing(6)
        self.streams_chip = QLabel("⊞ Flux: 0")
        self.streams_chip.setObjectName("StatusChip")
        self.displays_chip = QLabel("🖥 Écrans: 0")
        self.displays_chip.setObjectName("StatusChip")
        self.status_chip = QLabel("▶ Actifs: 0/0")
        self.status_chip.setObjectName("StatusChip")
        self.sender_chip = QLabel("📡 Émission: ⏹")
        self.sender_chip.setObjectName("SenderChipStopped")
        self.global_state_chip = QLabel("ARRÊTÉ")
        self.global_state_chip.setObjectName("GlobalStateStopped")
        chip_row.addWidget(self.streams_chip)
        chip_row.addWidget(self.displays_chip)
        chip_row.addWidget(self.status_chip)
        chip_row.addWidget(self.sender_chip)
        chip_row.addWidget(self.global_state_chip)
        chip_row.addStretch()

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.addSpacing(4)
        title_layout.addLayout(chip_row)

        actions_layout = QVBoxLayout()
        actions_layout.setAlignment(Qt.AlignVCenter)

        self.btn_toggle = QPushButton("▶  Démarrer tout")
        self.btn_toggle.setObjectName("SuccessButton")
        self.btn_toggle.clicked.connect(self.toggle_start_stop)
        self.btn_toggle.setMinimumWidth(180)
        self.btn_toggle.setMinimumHeight(42)
        actions_layout.addWidget(self.btn_toggle)

        header_layout.addLayout(title_layout, stretch=1)
        header_layout.addLayout(actions_layout)

        layout.addWidget(header_card)

        # ── Splitter ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        layout.addWidget(splitter, stretch=1)

        # ── Left panel (scrollable) ──
        left_scroll = QScrollArea()
        left_scroll.setObjectName("Card")
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.NoFrame)

        left_inner = QWidget()
        left_layout = QVBoxLayout(left_inner)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(14)

        # ── Displays group ──
        displays_group = QGroupBox("🖥  Écrans détectés")
        displays_layout = QVBoxLayout(displays_group)
        displays_layout.setSpacing(4)
        self.displays_list = QListWidget()
        self.displays_list.setSpacing(2)
        self.displays_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.displays_list.setMaximumHeight(140)
        displays_layout.addWidget(self.displays_list)

        displays_actions = QHBoxLayout()
        displays_actions.setSpacing(8)

        self.btn_auto_map = QPushButton("↪  Auto-mapper")
        self.btn_auto_map.setObjectName("PrimaryButton")
        self.btn_auto_map.setMinimumHeight(34)
        self.btn_auto_map.clicked.connect(self.auto_map_streams)
        displays_actions.addWidget(self.btn_auto_map)

        self.btn_rename_display = QPushButton("✎  Renommer")
        self.btn_rename_display.setMinimumHeight(34)
        self.btn_rename_display.clicked.connect(self.rename_selected_display)
        displays_actions.addWidget(self.btn_rename_display)

        self.btn_routing = QPushButton("🧭  Routage")
        self.btn_routing.setMinimumHeight(34)
        self.btn_routing.clicked.connect(self.open_routing_dialog)
        displays_actions.addWidget(self.btn_routing)

        displays_layout.addLayout(displays_actions)

        # ── Routing status group ──
        routes_group = QGroupBox("🧭  Routage")
        routes_layout = QVBoxLayout(routes_group)
        routes_layout.setSpacing(6)
        self.routes_status_list = QListWidget()
        self.routes_status_list.setSpacing(2)
        self.routes_status_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.routes_status_list.setMaximumHeight(150)
        routes_layout.addWidget(self.routes_status_list)

        # ── Preferences group ──
        prefs_group = QGroupBox("⚙  Préférences")
        prefs_layout = QVBoxLayout(prefs_group)
        self.exclude_primary = QCheckBox("Exclure l'écran principal")
        self.exclude_primary.setChecked(bool(self.config.get("excludePrimaryDisplay", True)))
        self.exclude_primary.stateChanged.connect(self.on_exclude_primary_changed)
        prefs_layout.addWidget(self.exclude_primary)

        rx_row = QHBoxLayout()
        rx_row.setSpacing(10)
        rx_lbl = QLabel("Réception")
        rx_lbl.setObjectName("FormLabel")
        rx_lbl.setFixedWidth(64)
        rx_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        rx_row.addWidget(rx_lbl)
        self.receiver_decode_combo = QComboBox()
        self.receiver_decode_combo.addItem("CPU", "cpu")
        self.receiver_decode_combo.addItem("GPU (Auto)", "auto")
        self.receiver_decode_combo.addItem("GPU (DXVA2)", "dxva2")
        self.receiver_decode_combo.addItem("GPU (AMF)", "h264_amf")
        self.receiver_decode_combo.addItem("GPU (CUVID)", "h264_cuvid")
        self.receiver_decode_combo.addItem("GPU (QSV)", "h264_qsv")
        self.receiver_decode_combo.setFixedHeight(28)
        rx_current = str((self.config.get("receiver") or {}).get("decode") or "cpu").strip().lower()
        rxi = self.receiver_decode_combo.findData(rx_current)
        if rxi >= 0:
            self.receiver_decode_combo.setCurrentIndex(rxi)
        self.receiver_decode_combo.currentIndexChanged.connect(self.on_receiver_changed)
        rx_row.addWidget(self.receiver_decode_combo, stretch=1)
        prefs_layout.addLayout(rx_row)

        self.auto_start_receiver_chk = QCheckBox("Auto-start réception")
        self.auto_start_receiver_chk.setChecked(bool(self.config.get("autoStartReceiver", False)))
        self.auto_start_receiver_chk.stateChanged.connect(self.on_auto_start_changed)
        prefs_layout.addWidget(self.auto_start_receiver_chk)

        self.auto_start_sender_chk = QCheckBox("Auto-start émission")
        self.auto_start_sender_chk.setChecked(bool(self.config.get("autoStartSender", False)))
        self.auto_start_sender_chk.stateChanged.connect(self.on_auto_start_changed)
        prefs_layout.addWidget(self.auto_start_sender_chk)

        self.btn_open_config_dir = QPushButton("📂  Ouvrir dossier config")
        self.btn_open_config_dir.setMinimumHeight(34)
        self.btn_open_config_dir.clicked.connect(self.open_config_directory)
        prefs_layout.addWidget(self.btn_open_config_dir)

        self.btn_reset_config = QPushButton("↺  Réinitialiser")
        self.btn_reset_config.setObjectName("DangerButton")
        self.btn_reset_config.setMinimumHeight(34)
        self.btn_reset_config.clicked.connect(self.reset_configuration)
        prefs_layout.addWidget(self.btn_reset_config)

        # ── Sender group ──
        sender_group = QGroupBox("📡  Émission OMT")
        sender_layout = QVBoxLayout(sender_group)
        sender_layout.setSpacing(10)

        def _form_label(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setObjectName("FormLabel")
            lbl.setFixedWidth(75)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return lbl

        sender_row1 = QHBoxLayout()
        sender_row1.setSpacing(8)
        sender_row1.addWidget(_form_label("Écran"))
        self.sender_display_combo = QComboBox()
        self.sender_display_combo.setFixedHeight(28)
        self.sender_display_combo.currentIndexChanged.connect(self.on_sender_changed)
        sender_row1.addWidget(self.sender_display_combo, stretch=1)
        sender_layout.addLayout(sender_row1)

        sender_row2 = QHBoxLayout()
        sender_row2.setSpacing(8)
        sender_row2.addWidget(_form_label("Nom OMT"))
        self.sender_name_edit = QLineEdit()
        self.sender_name_edit.setFixedHeight(28)
        self.sender_name_edit.setPlaceholderText("Nom publié sur le réseau (ex: SRT Multiview)")
        self.sender_name_edit.editingFinished.connect(self.on_sender_changed)
        sender_row2.addWidget(self.sender_name_edit, stretch=1)
        sender_layout.addLayout(sender_row2)

        sender_row3 = QHBoxLayout()
        sender_row3.setSpacing(8)
        sender_row3.addWidget(_form_label("FPS"))
        self.sender_fps_spin = QSpinBox()
        self.sender_fps_spin.setRange(1, 60)
        self.sender_fps_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.sender_fps_spin.setFixedHeight(28)
        self.sender_fps_spin.setFixedWidth(60)
        self.sender_fps_spin.valueChanged.connect(self.on_sender_changed)
        sender_row3.addWidget(self.sender_fps_spin)

        pf_lbl = QLabel("Pixel")
        pf_lbl.setObjectName("FormLabel")
        pf_lbl.setFixedWidth(40)
        pf_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        sender_row3.addWidget(pf_lbl)
        self.sender_pixfmt_combo = QComboBox()
        self.sender_pixfmt_combo.addItem("UYVY 4:2:2", "uyvy422")
        self.sender_pixfmt_combo.addItem("BGRA", "bgra")
        self.sender_pixfmt_combo.addItem("YUV422P10LE", "yuv422p10le")
        self.sender_pixfmt_combo.setFixedHeight(28)
        self.sender_pixfmt_combo.currentIndexChanged.connect(self.on_sender_changed)
        sender_row3.addWidget(self.sender_pixfmt_combo, stretch=1)
        sender_layout.addLayout(sender_row3)

        sender_row4 = QHBoxLayout()
        sender_row4.setSpacing(10)
        self.sender_clock_chk = QCheckBox("Clock output")
        self.sender_clock_chk.setToolTip("Active l'option libomt -clock_output 1")
        self.sender_clock_chk.stateChanged.connect(self.on_sender_changed)
        sender_row4.addWidget(self.sender_clock_chk)
        sender_layout.addLayout(sender_row4)

        sender_row5 = QHBoxLayout()
        sender_row5.setSpacing(10)
        self.btn_sender_toggle = QPushButton("▶  Émettre")
        self.btn_sender_toggle.setObjectName("SuccessButton")
        self.btn_sender_toggle.setMinimumHeight(38)
        self.btn_sender_toggle.clicked.connect(self.toggle_sender)
        sender_row5.addWidget(self.btn_sender_toggle, stretch=1)
        self.sender_status_label = QLabel("⏹ arrêté")
        self.sender_status_label.setObjectName("Subtitle")
        self.sender_status_label.setAlignment(Qt.AlignCenter)
        sender_row5.addWidget(self.sender_status_label)
        sender_layout.addLayout(sender_row5)

        left_layout.addWidget(displays_group)
        left_layout.addWidget(routes_group)
        left_layout.addWidget(prefs_group)
        left_layout.addWidget(sender_group)
        left_layout.addStretch()

        left_scroll.setWidget(left_inner)

        # ── Streams panel (right) ──
        streams_panel = QFrame()
        streams_panel.setObjectName("Card")
        streams_outer = QVBoxLayout(streams_panel)
        streams_outer.setContentsMargins(16, 16, 16, 16)
        streams_outer.setSpacing(12)

        streams_header = QHBoxLayout()
        streams_title = QLabel("Flux SRT entrants")
        streams_title.setObjectName("SectionTitle")
        streams_title_font = QFont("Bahnschrift", 13)
        streams_title_font.setWeight(QFont.DemiBold)
        streams_title.setFont(streams_title_font)

        self.streams_count_label = QLabel("")
        self.streams_count_label.setObjectName("Subtitle")

        self.btn_add = QPushButton("+  Ajouter un flux")
        self.btn_add.setObjectName("PrimaryButton")
        self.btn_add.clicked.connect(self.add_stream)

        streams_header.addWidget(streams_title)
        streams_header.addWidget(self.streams_count_label)
        streams_header.addStretch(1)
        streams_header.addWidget(self.btn_add)

        # ── Cards container (scrollable) ──
        self.streams_container = QWidget()
        self.streams_stack = QStackedLayout(self.streams_container)

        self.streams_scroll = QScrollArea()
        self.streams_scroll.setWidgetResizable(True)
        self.streams_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.streams_scroll.setFrameShape(QFrame.NoFrame)

        self.streams_inner = QWidget()
        self.streams_cards_layout = QVBoxLayout(self.streams_inner)
        self.streams_cards_layout.setContentsMargins(0, 0, 4, 0)
        self.streams_cards_layout.setSpacing(8)
        self.streams_cards_layout.addStretch()
        self.streams_scroll.setWidget(self.streams_inner)

        self.empty_placeholder = QLabel("Aucun flux configuré\nCliquez « + Ajouter un flux » pour commencer")
        self.empty_placeholder.setObjectName("EmptyPlaceholder")
        self.empty_placeholder.setAlignment(Qt.AlignCenter)
        self.empty_placeholder.setWordWrap(True)

        self.streams_stack.addWidget(self.streams_scroll)
        self.streams_stack.addWidget(self.empty_placeholder)

        streams_outer.addLayout(streams_header)
        streams_outer.addWidget(self.streams_container)

        self.stream_cards: list[dict] = []

        splitter.addWidget(left_scroll)
        splitter.addWidget(streams_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        left_scroll.setMinimumWidth(440)
        left_scroll.setMaximumWidth(440)
        streams_panel.setMinimumWidth(500)
        splitter.setSizes([460, 720])

        try:
            splitter.handle(1).setEnabled(False)
        except Exception:
            pass

        self.refresh_displays()
        self.reload_table()
        self.reload_sender_section()

        self.timer.start(1000)

        QTimer.singleShot(250, self.maybe_autostart)

    def on_exclude_primary_changed(self):
        self.config["excludePrimaryDisplay"] = bool(self.exclude_primary.isChecked())
        self.schedule_save()
        self.refresh_displays()
        self.reload_table()

    def on_auto_start_changed(self, *_args):
        self.config["autoStartReceiver"] = bool(self.auto_start_receiver_chk.isChecked())
        self.config["autoStartSender"] = bool(self.auto_start_sender_chk.isChecked())
        self.schedule_save()

    def open_routing_dialog(self):
        dlg = RoutingDialog(self)
        dlg.exec()
        self.config = core.load_config()
        self.refresh_displays()
        self.reload_table()
        self.reload_sender_section()

    def open_config_directory(self):
        config_dir = CONFIG_PATH.parent
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        target_url = QUrl.fromLocalFile(str(config_dir))
        if QDesktopServices.openUrl(target_url):
            return

        QMessageBox.warning(
            self,
            "Configuration",
            f"Impossible d'ouvrir le dossier de configuration.\n\n{config_dir}",
        )

    def refresh_routes_status(self):
        self.routes_status_list.clear()
        routes = self.config.get("routes") or []
        if not routes:
            item = QListWidgetItem("Aucune route")
            item.setForeground(QColor("#94a3b8"))
            self.routes_status_list.addItem(item)
            return

        status = core.route_manager.status()
        for r in routes:
            if not isinstance(r, dict):
                continue
            rid = str(r.get("id") or "")
            name = str(r.get("name") or rid)
            addr = str(r.get("multicastAddr") or "239.10.10.10").strip()
            try:
                port = int(r.get("multicastPort") or 0)
            except Exception:
                port = 0
            out = f"udp://@{addr}:{port}" if addr and port else ""
            running = bool(status.get(rid, False))
            prefix = "▶" if running else "⏹"
            label = f"{prefix} {name}"
            if out:
                label += f" — {out}"
            item = QListWidgetItem(label)
            item.setForeground(QColor("#50fa7b") if running else QColor("#94a3b8"))
            self.routes_status_list.addItem(item)

    def _route_by_id(self, route_id: str) -> dict | None:
        rid = str(route_id or "").strip()
        if not rid:
            return None
        for r in (self.config.get("routes") or []):
            if isinstance(r, dict) and str(r.get("id") or "") == rid:
                return r
        return None

    def _ensure_route_running(self, route_id: str) -> core.RouteLaunchResult:
        rid = str(route_id or "").strip()
        route = self._route_by_id(rid)
        if not route:
            return core.RouteLaunchResult(ok=False, reason="Route introuvable")
        if core.route_manager.status().get(rid, False):
            return core.RouteLaunchResult(ok=True)
        return core.route_manager.start_route(route)

    def _stream_for_player(self, stream: dict) -> tuple[dict, str | None]:
        source = str(stream.get("source") or "srt").strip().lower()
        if source != "route":
            return (dict(stream), None)

        rid = str(stream.get("sourceRouteId") or "").strip()
        if not rid:
            return ({}, "Sélectionne une route pour ce flux.")
        route = self._route_by_id(rid)
        if not route:
            return ({}, "La route sélectionnée n'existe plus.")

        stream_for_player = dict(stream)
        stream_for_player["source"] = "udp"
        stream_for_player["udpAddr"] = str(route.get("multicastAddr") or "").strip()
        stream_for_player["udpPort"] = int(route.get("multicastPort") or 0)
        return (stream_for_player, None)

    def _set_card_starting(self, row: int):
        if row < 0 or row >= len(self.stream_cards):
            return
        card_info = self.stream_cards[row]
        card_info["status_dot"].setObjectName("StatusDotStarting")
        card_info["status_label"].setText("démarrage")
        card_info["status_label"].setStyleSheet("color: #f59e0b; font-weight: 600;")
        card_info["start_btn"].setEnabled(False)
        card_info["status_dot"].style().unpolish(card_info["status_dot"])
        card_info["status_dot"].style().polish(card_info["status_dot"])
        card_info["card"].style().unpolish(card_info["card"])
        card_info["card"].style().polish(card_info["card"])

    def maybe_autostart(self):
        self.config = core.normalize_config(self.config)

        auto_rx = bool(self.config.get("autoStartReceiver"))
        auto_tx = bool(self.config.get("autoStartSender"))
        if not (auto_rx or auto_tx):
            return

        actions = []
        if auto_rx:
            actions.append("Réception")
        if auto_tx:
            actions.append("Émission")

        def _do_start():
            if auto_rx:
                self.start_all()
            if auto_tx:
                if not core.sender_manager.status():
                    self.toggle_sender()

        QTimer.singleShot(0, _do_start)

        def _show_waiting_dialog_if_needed():
            running_players = any(core.player_manager.status().values())
            running_sender = bool(core.sender_manager.status())
            if running_players or running_sender:
                return

            dlg = QDialog(self)
            dlg.setWindowTitle("Démarrage automatique")
            dlg.setAttribute(Qt.WA_DeleteOnClose, True)
            dlg.setModal(False)

            dlg_layout = QVBoxLayout(dlg)
            dlg_layout.setContentsMargins(18, 16, 18, 16)
            dlg_layout.setSpacing(12)

            label = QLabel(
                "Auto-start activé, mais aucun flux n'est actif pour l'instant.\n\n"
                "Actions configurées : "
                + ", ".join(actions)
                + "\n\n"
                "Si tes sources ne sont pas encore disponibles, c'est normal.\n"
                "L'app démarrera dès qu'elles arrivent."
            )
            label.setWordWrap(True)
            dlg_layout.addWidget(label)

            btn_row = QHBoxLayout()
            btn_row.addStretch(1)
            close_btn = QPushButton("Fermer")
            btn_row.addWidget(close_btn)
            dlg_layout.addLayout(btn_row)
            close_btn.clicked.connect(dlg.close)

            dlg.resize(480, 190)
            dlg.show()

            poll = QTimer(dlg)
            poll.setInterval(750)

            def _poll():
                if any(core.player_manager.status().values()) or core.sender_manager.status():
                    dlg.close()

            poll.timeout.connect(_poll)
            poll.start()

        QTimer.singleShot(900, _show_waiting_dialog_if_needed)

    def reset_configuration(self):
        reply = QMessageBox.question(
            self,
            "Réinitialisation",
            "Réinitialiser toute la configuration ?\n\n"
            "Cela supprimera :\n"
            "- les flux\n"
            "- le mapping flux → écrans\n"
            "- les noms d'écrans personnalisés\n"
            "- les routes de routage\n"
            "- les paramètres d'émission\n\n"
            "Les lectures/émissions en cours seront arrêtées.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.stop_all()

        for sid in list(core.player_manager.player_logs.keys()):
            core.player_manager.clear_logs(sid)
        self.pending_stream_starts.clear()

        self.config = {
            "streams": [],
            "mapping": {},
            "displayNames": {},
            "routes": [],
            "excludePrimaryDisplay": True,
            "autoStartReceiver": False,
            "autoStartSender": False,
            "sender": {
                "displayId": "",
                "name": "SRT Multiview",
                "fps": 30,
                "pixelFormat": "uyvy422",
                "clockOutput": False,
                "referenceLevel": 1.0,
            },
        }
        self.config = core.normalize_config(self.config)

        core.sender_manager.last_error = None

        self.exclude_primary.blockSignals(True)
        self.receiver_decode_combo.blockSignals(True)
        try:
            self.exclude_primary.setChecked(True)
            self.receiver_decode_combo.setCurrentIndex(self.receiver_decode_combo.findData("cpu"))
        finally:
            self.exclude_primary.blockSignals(False)
            self.receiver_decode_combo.blockSignals(False)

        self.auto_start_receiver_chk.blockSignals(True)
        self.auto_start_sender_chk.blockSignals(True)
        try:
            self.auto_start_receiver_chk.setChecked(False)
            self.auto_start_sender_chk.setChecked(False)
        finally:
            self.auto_start_receiver_chk.blockSignals(False)
            self.auto_start_sender_chk.blockSignals(False)

        core.save_config(self.config)

        self.refresh_displays()
        self.reload_table()
        self.reload_sender_section()
        self.refresh_routes_status()

    def refresh_displays(self):
        exclude = bool(self.config.get("excludePrimaryDisplay", True))
        overrides = self.config.get("displayNames", {})
        self.displays = core.get_displays(exclude_primary=exclude, name_overrides=overrides)
        self.sender_displays = core.get_displays(exclude_primary=False, name_overrides=overrides)
        self.render_displays()
        self.refresh_routes_status()
        self.reload_sender_section()
        self.update_header_chips()

    def reload_sender_section(self):
        sender = self.config.get("sender", {})
        current_display_id = str(sender.get("displayId") or "")

        self.sender_display_combo.blockSignals(True)
        self.sender_name_edit.blockSignals(True)
        self.sender_fps_spin.blockSignals(True)
        self.sender_pixfmt_combo.blockSignals(True)
        self.sender_clock_chk.blockSignals(True)
        try:
            self.sender_display_combo.clear()
            self.sender_display_combo.addItem("— Sélectionner —", "")
            known_ids = set()
            for d in self.sender_displays:
                did = str(d["id"])
                self.sender_display_combo.addItem(d["name"], did)
                known_ids.add(did)
            # Preserve a binding to a display not currently detected by adding a
            # ghost entry. This avoids wiping the user's choice on a transient
            # enumeration glitch (asleep monitor, slow driver init, etc.).
            if current_display_id and current_display_id not in known_ids:
                self.sender_display_combo.addItem(
                    f"⚠ Écran absent ({current_display_id})", current_display_id
                )
            idx = self.sender_display_combo.findData(current_display_id)
            if idx >= 0:
                self.sender_display_combo.setCurrentIndex(idx)

            self.sender_name_edit.setText(str(sender.get("name") or "SRT Multiview"))
            try:
                self.sender_fps_spin.setValue(int(sender.get("fps") or 30))
            except Exception:
                self.sender_fps_spin.setValue(30)
            pf = str(sender.get("pixelFormat") or "uyvy422").strip().lower()
            idx = self.sender_pixfmt_combo.findData(pf)
            if idx >= 0:
                self.sender_pixfmt_combo.setCurrentIndex(idx)
            self.sender_clock_chk.setChecked(bool(sender.get("clockOutput", False)))
        finally:
            self.sender_display_combo.blockSignals(False)
            self.sender_name_edit.blockSignals(False)
            self.sender_fps_spin.blockSignals(False)
            self.sender_pixfmt_combo.blockSignals(False)
            self.sender_clock_chk.blockSignals(False)

        self.refresh_sender_status()

    def on_sender_changed(self, *_args):
        sender = self.config.setdefault("sender", {})
        sender["displayId"] = str(self.sender_display_combo.currentData() or "")
        sender["name"] = self.sender_name_edit.text().strip() or "SRT Multiview"
        sender["fps"] = int(self.sender_fps_spin.value())
        sender["pixelFormat"] = str(self.sender_pixfmt_combo.currentData() or "uyvy422")
        sender["clockOutput"] = bool(self.sender_clock_chk.isChecked())
        self.schedule_save()

    def on_receiver_changed(self, *_args):
        receiver = self.config.setdefault("receiver", {})
        receiver["decode"] = str(self.receiver_decode_combo.currentData() or "cpu")
        self.schedule_save()

    def update_sender_toggle_button(self, is_running: bool):
        self.sender_is_running = bool(is_running)
        if is_running:
            self.btn_sender_toggle.setText("⏹  Arrêter")
            self.btn_sender_toggle.setObjectName("DangerButton")
        else:
            self.btn_sender_toggle.setText("▶  Émettre")
            self.btn_sender_toggle.setObjectName("SuccessButton")
        self.btn_sender_toggle.style().unpolish(self.btn_sender_toggle)
        self.btn_sender_toggle.style().polish(self.btn_sender_toggle)

    def refresh_sender_status(self):
        running = core.sender_manager.status()
        if running:
            self.sender_status_label.setText("▶ en cours")
            self.sender_status_label.setStyleSheet("color: #50fa7b;")
            self.sender_status_label.setToolTip("")
            self.sender_chip.setText("📡 Émission: ▶")
            self.sender_chip.setObjectName("SenderChipRunning")
        else:
            if getattr(core.sender_manager, "last_error", None):
                self.sender_status_label.setText("⏹ erreur")
                self.sender_status_label.setToolTip(str(core.sender_manager.last_error))
            else:
                self.sender_status_label.setText("⏹ arrêté")
                self.sender_status_label.setToolTip("")
            self.sender_status_label.setStyleSheet("color: #ff5555;")
            self.sender_chip.setText("📡 Émission: ⏹")
            self.sender_chip.setObjectName("SenderChipStopped")
        self.sender_chip.style().unpolish(self.sender_chip)
        self.sender_chip.style().polish(self.sender_chip)
        self.update_sender_toggle_button(running)

    def toggle_sender(self):
        if core.sender_manager.status():
            core.sender_manager.stop()
            self.refresh_sender_status()
            return

        self.on_sender_changed()
        sender = self.config.get("sender", {})
        display_id = str(sender.get("displayId") or "")
        if not display_id:
            QMessageBox.warning(self, "Émission OMT", "Sélectionne un écran à émettre.")
            return

        display = next((d for d in self.sender_displays if str(d.get("id")) == display_id), None)
        if not display:
            QMessageBox.warning(self, "Émission OMT", "L'écran sélectionné n'est plus disponible.")
            return

        result = core.sender_manager.start(
            display,
            name=str(sender.get("name") or "SRT Multiview"),
            fps=int(sender.get("fps") or 30),
            pixel_format=str(sender.get("pixelFormat") or "uyvy422"),
            clock_output=bool(sender.get("clockOutput", False)),
            reference_level=float(sender.get("referenceLevel", 1.0)),
        )
        if not result.ok:
            QMessageBox.warning(
                self,
                "Émission OMT",
                "Impossible de démarrer l'émission.\n\n" + (result.reason or "Erreur inconnue."),
            )
        self.refresh_sender_status()

    def _build_stream_card(self, stream: dict, row: int) -> dict:
        display_ids = {str(d["id"]) for d in self.displays}
        stream_id = str(stream.get("id"))

        card = QFrame()
        card.setObjectName("StreamCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(8)

        # ── Row 1: status dot + name + delete button ──
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        status_dot = QLabel("●")
        status_dot.setObjectName("StatusDotStopped")
        status_dot.setFixedWidth(20)
        status_dot.setAlignment(Qt.AlignCenter)
        top_row.addWidget(status_dot)

        name_edit = QLineEdit(str(stream.get("name", "")))
        name_edit.setFixedHeight(28)
        name_edit.setPlaceholderText("Nom du flux")
        name_edit.editingFinished.connect(lambda r=row: self._on_card_changed(r))
        top_row.addWidget(name_edit, stretch=1)

        status_label = QLabel("arrêté")
        status_label.setObjectName("Subtitle")
        status_label.setFixedWidth(60)
        status_label.setAlignment(Qt.AlignCenter)
        top_row.addWidget(status_label)

        start_btn = QPushButton("▶")
        start_btn.setFixedSize(30, 24)
        start_btn.setToolTip("Démarrer/arrêter ce flux")
        start_btn.clicked.connect(lambda checked=False, r=row: self.toggle_stream(r))
        top_row.addWidget(start_btn)

        log_btn = QPushButton("📋")
        log_btn.setFixedSize(30, 24)
        log_btn.setToolTip("Voir la commande et les logs ffplay")
        log_btn.clicked.connect(lambda checked=False, r=row: self.show_stream_log(r))
        top_row.addWidget(log_btn)

        delete_btn = QPushButton("✕")
        delete_btn.setObjectName("CardDeleteBtn")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setToolTip("Supprimer ce flux")
        delete_btn.clicked.connect(lambda checked=False, r=row: self._delete_stream(r))
        top_row.addWidget(delete_btn)

        card_layout.addLayout(top_row)

        fields = QGridLayout()
        fields.setHorizontalSpacing(10)
        fields.setVerticalSpacing(6)

        source_lbl = QLabel("Source")
        source_lbl.setObjectName("FormLabel")
        source_lbl.setFixedWidth(54)
        source_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        source_combo = QComboBox()
        source_combo.addItem("SRT", "srt")
        source_combo.addItem("Route", "route")
        source_combo.addItem("OMT", "omt")
        source_combo.setFixedHeight(28)
        current_source = str(stream.get("source") or "srt").strip().lower()
        is_route_source = current_source == "route"
        is_omt_source = current_source == "omt"
        idx = source_combo.findData(current_source)
        if idx >= 0:
            source_combo.setCurrentIndex(idx)
        source_combo.currentIndexChanged.connect(lambda _v, r=row: self._on_source_changed(r))

        route_combo = QComboBox()
        route_combo.addItem("— Sélectionner —", "")
        for r in (self.config.get("routes") or []):
            if isinstance(r, dict):
                rid = str(r.get("id") or "")
                rname = str(r.get("name") or rid)
                if rid:
                    route_combo.addItem(rname, rid)
        route_combo.setFixedHeight(28)
        current_route_id = str(stream.get("sourceRouteId") or "")
        ridx = route_combo.findData(current_route_id)
        if ridx >= 0:
            route_combo.setCurrentIndex(ridx)
        route_combo.setEnabled(is_route_source)
        route_combo.setVisible(is_route_source)
        route_combo.currentIndexChanged.connect(lambda _v, r=row: self._on_card_changed(r))

        omt_edit = QLineEdit(str(stream.get("omtSource") or ""))
        omt_edit.setPlaceholderText("HOST (Source Name)")
        omt_edit.setFixedHeight(28)
        omt_edit.editingFinished.connect(lambda r=row: self._on_card_changed(r))
        omt_edit.setVisible(is_omt_source)

        omt_btn = QPushButton("🔍")
        omt_btn.setToolTip("Découvrir les sources OMT du réseau")
        omt_btn.setFixedSize(30, 28)
        omt_btn.clicked.connect(lambda _c=False, r=row: self._discover_omt_source(r))
        omt_btn.setVisible(is_omt_source)

        fields.addWidget(source_lbl, 0, 0)
        if is_route_source:
            fields.addWidget(source_combo, 0, 1)
            fields.addWidget(route_combo, 0, 2, 1, 4)
        elif is_omt_source:
            fields.addWidget(source_combo, 0, 1)
            fields.addWidget(omt_edit, 0, 2, 1, 3)
            fields.addWidget(omt_btn, 0, 5)
        else:
            fields.addWidget(source_combo, 0, 1, 1, 5)
            route_combo.hide()
            omt_edit.hide()
            omt_btn.hide()

        # ── Row 2: port + latency + mute ──

        port_lbl = QLabel("Port")
        port_lbl.setObjectName("FormLabel")
        port_lbl.setFixedWidth(30)
        port_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        port_spin = QSpinBox()
        port_spin.setRange(1, 65535)
        port_spin.setValue(int(stream.get("port", 9000)))
        port_spin.setButtonSymbols(QSpinBox.NoButtons)
        port_spin.setFixedHeight(28)
        port_spin.setFixedWidth(70)
        port_spin.setEnabled(current_source == "srt")
        port_spin.valueChanged.connect(lambda v, r=row: self._on_card_changed(r))

        lat_lbl = QLabel("Latence")
        lat_lbl.setObjectName("FormLabel")
        lat_lbl.setFixedWidth(48)
        lat_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        latency_spin = QSpinBox()
        latency_spin.setRange(0, 5000)
        latency_spin.setValue(int(stream.get("latency", 120)))
        latency_spin.setSuffix(" ms")
        latency_spin.setButtonSymbols(QSpinBox.NoButtons)
        latency_spin.setFixedHeight(28)
        latency_spin.setFixedWidth(80)
        latency_spin.setEnabled(current_source == "srt")
        latency_spin.valueChanged.connect(lambda v, r=row: self._on_card_changed(r))

        mute_chk = QCheckBox("Muet")
        mute_chk.setChecked(bool(stream.get("muteAudio")))
        mute_chk.setToolTip("Couper l'audio de ce flux")
        mute_chk.stateChanged.connect(lambda _v, r=row: self._on_card_changed(r))

        fields.addWidget(port_lbl, 1, 0)
        fields.addWidget(port_spin, 1, 1)
        fields.addWidget(lat_lbl, 1, 2)
        fields.addWidget(latency_spin, 1, 3)
        fields.addWidget(mute_chk, 1, 4, 1, 2)

        # ── Row 3: mode + rotation + screen ──

        mode_lbl = QLabel("Mode")
        mode_lbl.setObjectName("FormLabel")
        mode_lbl.setFixedWidth(38)
        mode_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        mode_combo = QComboBox()
        mode_combo.addItem("Fit", "fit")
        mode_combo.addItem("Fill", "fill")
        mode_combo.addItem("Stretch", "stretch")
        mode_combo.setFixedHeight(28)
        current_mode = str(stream.get("displayMode") or "fit").strip().lower()
        idx = mode_combo.findData(current_mode)
        if idx >= 0:
            mode_combo.setCurrentIndex(idx)
        mode_combo.currentIndexChanged.connect(lambda _v, r=row: self._on_card_changed(r))

        rot_lbl = QLabel("Rot")
        rot_lbl.setObjectName("FormLabel")
        rot_lbl.setFixedWidth(26)
        rot_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        rot_combo = QComboBox()
        rot_combo.addItem("0°", 0)
        rot_combo.addItem("90°", 90)
        rot_combo.addItem("180°", 180)
        rot_combo.addItem("270°", 270)
        rot_combo.setFixedHeight(28)
        try:
            current_rot = int(stream.get("rotate") or 0)
        except Exception:
            current_rot = 0
        ridx = rot_combo.findData(current_rot)
        if ridx >= 0:
            rot_combo.setCurrentIndex(ridx)
        rot_combo.currentIndexChanged.connect(lambda _v, r=row: self._on_card_changed(r))

        screen_lbl = QLabel("Écran")
        screen_lbl.setObjectName("FormLabel")
        screen_lbl.setFixedWidth(38)
        screen_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        display_combo = QComboBox()
        display_combo.addItem("— Non assigné —", "")
        for d in self.displays:
            display_combo.addItem(d["name"], str(d["id"]))
        display_combo.setFixedHeight(28)

        current_display_id = self.config.get("mapping", {}).get(stream_id)
        if current_display_id:
            cid = str(current_display_id)
            # Preserve binding to a display that isn't currently detected
            # (asleep monitor, slow driver init…) by adding a ghost entry.
            if cid not in display_ids:
                display_combo.addItem(f"⚠ Écran absent ({cid})", cid)
            idx = display_combo.findData(cid)
            if idx >= 0:
                display_combo.setCurrentIndex(idx)

        display_combo.currentIndexChanged.connect(lambda v, r=row: self._on_card_changed(r))

        fields.addWidget(mode_lbl, 2, 0)
        fields.addWidget(mode_combo, 2, 1)
        fields.addWidget(rot_lbl, 2, 2)
        fields.addWidget(rot_combo, 2, 3)
        fields.addWidget(screen_lbl, 2, 4)
        fields.addWidget(display_combo, 2, 5)

        fields.setColumnStretch(5, 1)
        card_layout.addLayout(fields)

        return {
            "card": card,
            "fields": fields,
            "name_edit": name_edit,
            "port_spin": port_spin,
            "latency_spin": latency_spin,
            "mute_chk": mute_chk,
            "mode_combo": mode_combo,
            "rot_combo": rot_combo,
            "source_combo": source_combo,
            "route_combo": route_combo,
            "omt_edit": omt_edit,
            "omt_btn": omt_btn,
            "display_combo": display_combo,
            "status_dot": status_dot,
            "status_label": status_label,
            "start_btn": start_btn,
            "log_btn": log_btn,
            "stream_id": stream_id,
        }

    def toggle_stream(self, row: int):
        self.config = core.normalize_config(self.config)
        streams = self.config.get("streams", [])
        if row < 0 or row >= len(streams):
            return
        if row >= len(self.stream_cards):
            return

        self._update_config_from_card(row)
        self.config = core.normalize_config(self.config)
        core.save_config(self.config)

        stream = self.config.get("streams", [])[row]
        stream_id = str(stream.get("id"))
        running = bool(core.player_manager.status().get(stream_id, False))

        if running:
            self.pending_stream_starts.pop(stream_id, None)
            core.player_manager.stop_player(stream_id)
            self.refresh_status()
            return

        display_id = str((self.config.get("mapping", {}) or {}).get(stream_id) or "")
        if not display_id:
            QMessageBox.warning(self, "Démarrage flux", "Assigne un écran à ce flux avant de le démarrer.")
            return

        display = next((d for d in self.displays if str(d.get("id")) == display_id), None)
        if not display:
            QMessageBox.warning(self, "Démarrage flux", "L'écran assigné n'est plus disponible.")
            return

        source = str(stream.get("source") or "srt").strip().lower()
        startup_seconds = 0.8
        if source == "route":
            startup_seconds = 3.5
            rid = str(stream.get("sourceRouteId") or "").strip()
            result = self._ensure_route_running(rid)
            if not result.ok:
                QMessageBox.warning(self, "Démarrage flux", "Impossible de démarrer la route.\n\n" + (result.reason or "Erreur inconnue."))
                return

        stream_for_player, err = self._stream_for_player(stream)
        if err:
            QMessageBox.warning(self, "Démarrage flux", err)
            return

        if str(stream_for_player.get("source") or "").strip().lower() == "udp":
            startup_seconds = max(startup_seconds, 3.5)

        self.pending_stream_starts[stream_id] = time.monotonic() + float(startup_seconds)
        self._set_card_starting(row)

        hwaccel = str((self.config.get("receiver") or {}).get("decode") or "cpu").strip().lower()
        if hwaccel == "gpu":
            hwaccel = "auto"
        if hwaccel not in {"cpu", "auto", "dxva2", "h264_amf", "h264_cuvid", "h264_qsv"}:
            hwaccel = "cpu"

        result = core.player_manager.start_player(stream_for_player, display, hwaccel=hwaccel)
        if not result.ok:
            self.pending_stream_starts.pop(stream_id, None)
            QMessageBox.warning(self, "Démarrage flux", "Impossible de démarrer le flux.\n\n" + (result.reason or "Erreur inconnue."))
        self.refresh_status()

    def show_stream_log(self, row: int):
        streams = self.config.get("streams", [])
        if row < 0 or row >= len(streams):
            return

        stream = streams[row]
        stream_id = str(stream.get("id") or "")
        if not stream_id:
            return

        info = core.player_manager.debug_info(stream_id)
        stderr_lines = info.get("stderr") or []
        launch_error = str(info.get("launch_error") or "").strip()
        command_text = str(info.get("command_text") or "").strip()
        debug_text = "\n\n".join(
            [
                f"Binaire: {info.get('path') or ''}",
                f"PID: {info.get('pid') or '—'}",
                f"En cours: {'oui' if info.get('running') else 'non'}",
                f"Code retour: {info.get('returncode') if info.get('returncode') is not None else '—'}",
                "Commande:",
                command_text or "—",
                "Erreur de lancement:" if launch_error else "",
                launch_error,
                "stderr:",
                "\n".join(str(line) for line in stderr_lines) if stderr_lines else "—",
            ]
        ).strip()

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Logs ffplay — {stream.get('name') or stream_id}")
        dlg.setMinimumSize(760, 520)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setLineWrapMode(QPlainTextEdit.NoWrap)
        text.setPlainText(debug_text)
        layout.addWidget(text)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        copy_btn = QPushButton("Copier")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(debug_text))
        btn_row.addWidget(copy_btn)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)
        dlg.exec()

    def reload_table(self):
        self.config = core.normalize_config(self.config)
        streams = self.config.get("streams", [])

        # Clear existing cards
        for card_info in self.stream_cards:
            card_info["card"].setParent(None)
            card_info["card"].deleteLater()
        self.stream_cards.clear()

        # Remove stretch item
        while self.streams_cards_layout.count():
            item = self.streams_cards_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self.streams_stack.setCurrentIndex(1 if len(streams) == 0 else 0)
        self.streams_count_label.setText(f"({len(streams)})" if streams else "")

        for row, stream in enumerate(streams):
            card_info = self._build_stream_card(stream, row)
            self.streams_cards_layout.addWidget(card_info["card"])
            self.stream_cards.append(card_info)

        self.streams_cards_layout.addStretch()
        self.refresh_status()

    def _on_card_changed(self, row: int):
        self._update_config_from_card(row)
        self.schedule_save()

    def _on_source_changed(self, row: int):
        if row < 0 or row >= len(self.stream_cards):
            return
        card = self.stream_cards[row]
        source = str(card["source_combo"].currentData() or "srt")
        grid = card.get("fields")
        if isinstance(grid, QGridLayout):
            for key in ("source_combo", "route_combo", "omt_edit", "omt_btn"):
                try:
                    grid.removeWidget(card[key])
                except Exception:
                    pass

            if source == "route":
                grid.addWidget(card["source_combo"], 0, 1)
                grid.addWidget(card["route_combo"], 0, 2, 1, 4)
                card["route_combo"].show()
                card["omt_edit"].hide()
                card["omt_btn"].hide()
            elif source == "omt":
                grid.addWidget(card["source_combo"], 0, 1)
                grid.addWidget(card["omt_edit"], 0, 2, 1, 3)
                grid.addWidget(card["omt_btn"], 0, 5)
                card["omt_edit"].show()
                card["omt_btn"].show()
                card["route_combo"].hide()
            else:
                grid.addWidget(card["source_combo"], 0, 1, 1, 5)
                card["route_combo"].hide()
                card["omt_edit"].hide()
                card["omt_btn"].hide()
        card["route_combo"].setEnabled(source == "route")
        card["omt_edit"].setEnabled(source == "omt")
        card["omt_btn"].setEnabled(source == "omt")
        card["port_spin"].setEnabled(source == "srt")
        card["latency_spin"].setEnabled(source == "srt")
        if source != "route":
            card["route_combo"].setCurrentIndex(0)
        if source != "omt":
            card["omt_edit"].clear()
        self._on_card_changed(row)

    def _discover_omt_source(self, row: int):
        if row < 0 or row >= len(self.stream_cards):
            return
        card = self.stream_cards[row]
        current = card["omt_edit"].text().strip()
        dlg = OMTDiscoveryDialog(self, current=current)
        if dlg.exec() == QDialog.Accepted and dlg.selected_source:
            card["omt_edit"].setText(dlg.selected_source)
            self._on_card_changed(row)

    def _delete_stream(self, row: int):
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
        core.player_manager.clear_logs(stream_id)
        self.pending_stream_starts.pop(stream_id, None)
        streams.pop(row)
        self.config.get("mapping", {}).pop(stream_id, None)
        self.reload_table()
        self.schedule_save()

    def schedule_save(self):
        self.autosave_timer.start(500)

    def _update_config_from_card(self, row: int):
        streams = self.config.get("streams", [])
        if row < 0 or row >= len(streams) or row >= len(self.stream_cards):
            return

        stream = streams[row]
        stream_id = str(stream.get("id"))
        card = self.stream_cards[row]

        stream["name"] = card["name_edit"].text().strip() or stream_id
        stream["port"] = int(card["port_spin"].value())
        stream["latency"] = int(card["latency_spin"].value())
        stream["muteAudio"] = bool(card["mute_chk"].isChecked())
        stream["displayMode"] = str(card["mode_combo"].currentData() or "fit")
        stream["rotate"] = int(card["rot_combo"].currentData() or 0)

        source = str(card["source_combo"].currentData() or "srt")
        stream["source"] = source
        stream["sourceRouteId"] = (
            str(card["route_combo"].currentData() or "") if source == "route" else ""
        )
        stream["omtSource"] = (
            card["omt_edit"].text().strip() if source == "omt" else ""
        )

        display_id = card["display_combo"].currentData() or ""
        mapping = self.config.setdefault("mapping", {})
        if display_id:
            mapping[stream_id] = str(display_id)
        else:
            mapping.pop(stream_id, None)

    def save(self):
        for row in range(len(self.stream_cards)):
            self._update_config_from_card(row)

        self.config = core.normalize_config(self.config)
        core.save_config(self.config)

    def check_duplicate_ports(self) -> list[int]:
        streams = self.config.get("streams", [])
        ports = [s.get("port") for s in streams if str(s.get("source") or "srt").strip().lower() == "srt"]
        seen = set()
        duplicates = set()
        for p in ports:
            if p in seen:
                duplicates.add(p)
            seen.add(p)
        return list(duplicates)

    def start_all(self):
        self.save()

        streams = self.config.get("streams", [])
        needs_udp_startup = any(
            isinstance(s, dict) and str(s.get("source") or "srt").strip().lower() == "route" for s in (streams or [])
        )
        startup_seconds = 3.5 if needs_udp_startup else 1.0
        self.global_start_until = time.monotonic() + float(startup_seconds)
        self.btn_toggle.setText("⏹  Annuler")
        self.btn_toggle.setObjectName("DangerButton")
        self.btn_toggle.setEnabled(True)
        self.btn_toggle.style().unpolish(self.btn_toggle)
        self.btn_toggle.style().polish(self.btn_toggle)

        duplicate_ports = self.check_duplicate_ports()
        if duplicate_ports:
            QMessageBox.warning(
                self,
                "Ports en double",
                "Attention : les ports suivants sont utilisés plusieurs fois :\n"
                + ", ".join(map(str, duplicate_ports))
                + "\n\nCela peut causer des conflits.",
            )

        routes_needed: set[str] = set()
        for s in (self.config.get("streams") or []):
            if not isinstance(s, dict):
                continue
            if str(s.get("source") or "srt").strip().lower() != "route":
                continue
            rid = str(s.get("sourceRouteId") or "").strip()
            if rid:
                routes_needed.add(rid)

        if routes_needed:
            routes_by_id = {str(r.get("id")): r for r in (self.config.get("routes") or []) if isinstance(r, dict)}
            running_routes = core.route_manager.status()
            for rid in sorted(routes_needed):
                if running_routes.get(rid, False):
                    continue
                route = routes_by_id.get(rid)
                if not route:
                    continue
                self._ensure_route_running(rid)

        results = core.apply_mapping(self.config)
        stream_name_by_id = {str(s.get("id")): str(s.get("name") or s.get("id")) for s in self.config.get("streams", [])}
        failures = [
            f"{stream_name_by_id.get(str(sid), str(sid))} — {(res.reason or 'Erreur inconnue.') }"
            for sid, res in results.items()
            if not res.ok and res.reason != "NO_DISPLAY"
        ]
        self.refresh_status()

        if failures:
            QMessageBox.warning(
                self,
                "Démarrage partiel",
                "Certains flux n'ont pas démarré (pas d'écran assigné, ou ffplay manquant).\n\n"
                + "\n".join(failures),
            )
        status = core.player_manager.status()
        self.update_toggle_button(any(status.values()))

    def stop_all(self):
        self.global_start_until = None
        core.player_manager.stop_all()
        core.sender_manager.stop()
        core.route_manager.stop_all()
        self.refresh_status()
        self.refresh_sender_status()
        self.update_toggle_button(False)

    def toggle_start_stop(self):
        if self.global_start_until is not None:
            self.stop_all()
            return
        if self.is_running:
            self.stop_all()
        else:
            self.start_all()

    def update_toggle_button(self, is_running: bool):
        self.is_running = is_running
        if is_running:
            self.btn_toggle.setText("⏹  Tout arrêter")
            self.btn_toggle.setObjectName("DangerButton")
        else:
            self.btn_toggle.setText("▶  Démarrer tout")
            self.btn_toggle.setObjectName("SuccessButton")
        self.btn_toggle.setEnabled(True)
        self.btn_toggle.style().unpolish(self.btn_toggle)
        self.btn_toggle.style().polish(self.btn_toggle)

    def refresh_status(self):
        status = core.player_manager.status()
        streams = self.config.get("streams", [])

        now = time.monotonic()

        for row, stream in enumerate(streams):
            if row >= len(self.stream_cards):
                break
            stream_id = str(stream.get("id"))
            running = status.get(stream_id, False)
            card_info = self.stream_cards[row]

            pending_until = self.pending_stream_starts.get(stream_id)
            is_starting = bool(pending_until and now < float(pending_until))
            if pending_until and not is_starting:
                self.pending_stream_starts.pop(stream_id, None)

            if is_starting:
                card_info["status_dot"].setObjectName("StatusDotStarting")
                card_info["status_label"].setText("démarrage")
                card_info["status_label"].setStyleSheet("color: #f59e0b; font-weight: 600;")
                card_info["card"].setObjectName("StreamCard")
                card_info["start_btn"].setText("…")
                card_info["start_btn"].setObjectName("PrimaryButton")
                card_info["start_btn"].setEnabled(False)
            elif running:
                card_info["status_dot"].setObjectName("StatusDotRunning")
                card_info["status_label"].setText("en cours")
                card_info["status_label"].setStyleSheet("color: #50fa7b; font-weight: 600;")
                card_info["card"].setObjectName("StreamCardRunning")
                card_info["start_btn"].setText("⏹")
                card_info["start_btn"].setObjectName("DangerButton")
                card_info["start_btn"].setEnabled(True)
            else:
                card_info["status_dot"].setObjectName("StatusDotStopped")
                card_info["status_label"].setText("arrêté")
                card_info["status_label"].setStyleSheet("color: #64748b;")
                card_info["card"].setObjectName("StreamCard")
                card_info["start_btn"].setText("▶")
                card_info["start_btn"].setObjectName("SuccessButton")
                card_info["start_btn"].setEnabled(True)

            card_info["status_dot"].style().unpolish(card_info["status_dot"])
            card_info["status_dot"].style().polish(card_info["status_dot"])
            card_info["card"].style().unpolish(card_info["card"])
            card_info["card"].style().polish(card_info["card"])
            card_info["start_btn"].style().unpolish(card_info["start_btn"])
            card_info["start_btn"].style().polish(card_info["start_btn"])

        self.update_header_chips(status)
        any_running = any(status.values())
        if any_running:
            self.global_start_until = None
        if self.global_start_until is not None and not any_running and now < float(self.global_start_until):
            self.btn_toggle.setText("⏹  Annuler")
            self.btn_toggle.setObjectName("DangerButton")
            self.btn_toggle.setEnabled(True)
            self.btn_toggle.style().unpolish(self.btn_toggle)
            self.btn_toggle.style().polish(self.btn_toggle)
        else:
            if self.global_start_until is not None and not any_running:
                self.global_start_until = None
            self.update_toggle_button(any_running)
        self.refresh_sender_status()
        self.refresh_routes_status()

    def _next_free_srt_port(self, start: int = 9001) -> int:
        used = {
            int(s.get("port") or 0)
            for s in (self.config.get("streams") or [])
            if isinstance(s, dict)
        }
        port = max(int(start), 1)
        while port in used and port < 65535:
            port += 1
        return port

    def add_stream(self):
        next_index = len(self.config.get("streams", [])) + 1
        stream_id = f"stream-{uuid.uuid4().hex[:12]}"
        port = self._next_free_srt_port(9000 + next_index)
        self.config.setdefault("streams", []).append(
            {"id": stream_id, "name": f"Flux {next_index}", "port": port, "latency": 120}
        )
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
            item.setData(Qt.UserRole, str(display["id"]))
            self.displays_list.addItem(item)

    def auto_map_streams(self):
        self.config = core.normalize_config(self.config)
        streams = self.config.get("streams", [])

        displays = list(self.displays)
        if not displays:
            QMessageBox.warning(self, "Auto-mapping", "Aucun écran disponible pour mapper les flux.")
            return

        target_count = len(displays)
        if len(streams) < target_count:
            used_ports = {int(s.get("port") or 0) for s in streams if isinstance(s, dict)}

            def _next_free_port(start: int = 9001) -> int:
                p = int(start)
                while p in used_ports or p <= 0:
                    p += 1
                used_ports.add(p)
                return p

            start_index = len(streams)
            for i in range(start_index, target_count):
                stream_id = f"stream-{uuid.uuid4().hex[:12]}"
                port = _next_free_port(9000 + i + 1)
                streams.append({"id": stream_id, "name": f"Flux {i + 1}", "port": port, "latency": 120})

            self.config["streams"] = streams
            self.config = core.normalize_config(self.config)

        display_ids = [str(d.get("id")) for d in displays]
        mapping = self.config.setdefault("mapping", {})
        used: set[str] = set(str(v) for v in mapping.values() if v)

        next_index = 0
        for stream in streams:
            stream_id = str(stream.get("id"))
            current = mapping.get(stream_id)
            if current and str(current) in display_ids:
                continue

            while next_index < len(display_ids) and display_ids[next_index] in used:
                next_index += 1
            if next_index >= len(display_ids):
                mapping.pop(stream_id, None)
                continue

            mapping[stream_id] = display_ids[next_index]
            used.add(display_ids[next_index])
            next_index += 1

        self.reload_table()
        self.schedule_save()

    def rename_selected_display(self):
        item = self.displays_list.currentItem()
        if not item:
            return
        display_id = item.data(Qt.UserRole)
        if not display_id:
            return

        current_name = ""
        for d in self.displays:
            if str(d.get("id")) == str(display_id):
                current_name = str(d.get("name") or "")
                break

        new_name, ok = QInputDialog.getText(self, "Renommer écran", "Nom de l'écran :", text=current_name)
        if not ok:
            return
        new_name = (new_name or "").strip()
        if not new_name:
            QMessageBox.warning(self, "Renommer écran", "Le nom ne peut pas être vide.")
            return

        names = self.config.setdefault("displayNames", {})
        names[str(display_id)] = str(new_name)
        self.schedule_save()
        self.refresh_displays()
        self.reload_table()

    def update_header_chips(self, status: dict | None = None):
        stream_count = len(self.config.get("streams", []))
        display_count = len(self.displays)
        if status is None:
            status = core.player_manager.status()
        active_count = sum(1 for value in status.values() if value)

        sender_running = core.sender_manager.status()

        self.streams_chip.setText(f"⊞ Flux: {stream_count}")
        self.displays_chip.setText(f"🖥 Écrans: {display_count}")
        self.status_chip.setText(f"▶ Actifs: {active_count}/{stream_count}")

        if sender_running:
            self.sender_chip.setText("📡 Émission: ▶")
            self.sender_chip.setObjectName("SenderChipRunning")
        else:
            self.sender_chip.setText("📡 Émission: ⏹")
            self.sender_chip.setObjectName("SenderChipStopped")
        self.sender_chip.style().unpolish(self.sender_chip)
        self.sender_chip.style().polish(self.sender_chip)

        if active_count > 0:
            self.global_state_chip.setText("EN COURS")
            self.global_state_chip.setObjectName("GlobalStateRunning")
        else:
            self.global_state_chip.setText("ARRÊTÉ")
            self.global_state_chip.setObjectName("GlobalStateStopped")
        self.global_state_chip.style().unpolish(self.global_state_chip)
        self.global_state_chip.style().polish(self.global_state_chip)

    def closeEvent(self, event):
        # Flush any pending autosave before tearing everything down.
        if self.autosave_timer.isActive():
            self.autosave_timer.stop()
        try:
            self.save()
        except Exception:
            pass
        core.player_manager.stop_all()
        core.sender_manager.stop()
        core.route_manager.stop_all()
        event.accept()


def main() -> None:
    enable_hi_dpi()

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
