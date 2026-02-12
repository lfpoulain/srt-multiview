import sys
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedLayout,
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
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: 0.5px;
}
QLabel#Subtitle {
    color: #94a3b8;
    font-size: 11px;
}
QLabel#SectionTitle {
    font-size: 13px;
    font-weight: 600;
    color: #e2e8f0;
}
QLabel#StatusChip {
    background: #1e293b;
    color: #e2e8f0;
    padding: 4px 14px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
}
QLabel#SenderChipRunning {
    background: #14532d;
    color: #86efac;
    padding: 4px 14px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}
QLabel#SenderChipStopped {
    background: #1e293b;
    color: #94a3b8;
    padding: 4px 14px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
}
QFrame#Card, QGroupBox {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
}
QGroupBox {
    font-weight: 600;
    padding-top: 20px;
    margin-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #cbd5f5;
    font-size: 12px;
}
QPushButton {
    background: #1f2937;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 500;
}
QPushButton:hover {
    background: #263247;
    border-color: #475569;
}
QPushButton:pressed {
    background: #1a202e;
}
QPushButton#PrimaryButton {
    background: #2563eb;
    border-color: #1d4ed8;
    color: #ffffff;
}
QPushButton#PrimaryButton:hover {
    background: #3b82f6;
}
QPushButton#PrimaryButton:pressed {
    background: #1d4ed8;
}
QPushButton#SuccessButton {
    background: #16a34a;
    border-color: #15803d;
    color: #ffffff;
}
QPushButton#SuccessButton:hover {
    background: #22c55e;
}
QPushButton#SuccessButton:pressed {
    background: #15803d;
}
QPushButton#DangerButton {
    background: #dc2626;
    border-color: #b91c1c;
    color: #ffffff;
}
QPushButton#DangerButton:hover {
    background: #ef4444;
}
QPushButton#DangerButton:pressed {
    background: #b91c1c;
}
QLineEdit, QSpinBox, QComboBox {
    background: #0b1220;
    border: 1px solid #1f2937;
    border-radius: 6px;
    padding: 4px 8px;
    selection-background-color: #334155;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #6366f1;
}
QListWidget {
    background: #0b1220;
    border: 1px solid #1f2937;
    border-radius: 10px;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 6px;
}
QListWidget::item:selected {
    background: #1f2937;
}
QSplitter::handle {
    background: transparent;
    width: 8px;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px 0;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0 4px;
}
QScrollBar::handle:horizontal {
    background: #334155;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #475569;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #475569;
    background: #1e293b;
}
QCheckBox::indicator:checked {
    background: #6366f1;
    border-color: #6366f1;
}
QLabel#FormLabel {
    color: #94a3b8;
    font-size: 11px;
    min-width: 70px;
}
QLabel#EmptyPlaceholder {
    color: #475569;
    font-size: 13px;
    font-style: italic;
}
QFrame#StreamCard {
    background: #0f172a;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 0px;
}
QFrame#StreamCard:hover {
    border-color: #334155;
}
QFrame#StreamCardRunning {
    background: #0f172a;
    border: 1px solid #166534;
    border-radius: 10px;
    padding: 0px;
}
QLabel#StreamName {
    font-size: 13px;
    font-weight: 600;
    color: #f1f5f9;
}
QLabel#StatusDotRunning {
    color: #22c55e;
    font-size: 18px;
}
QLabel#StatusDotStopped {
    color: #475569;
    font-size: 18px;
}
QPushButton#CardDeleteBtn {
    background: transparent;
    border: none;
    color: #64748b;
    font-size: 14px;
    padding: 2px 6px;
    border-radius: 4px;
}
QPushButton#CardDeleteBtn:hover {
    background: #7f1d1d;
    color: #fca5a5;
}
"""

DRACULA_OVERLAY_QSS = """
QLabel#Title {
    font-size: 22px;
    font-weight: 700;
    color: #f8f8f2;
}
QLabel#Subtitle {
    color: #6272a4;
    font-size: 11px;
}
QLabel#StatusChip {
    background: #44475a;
    color: #f8f8f2;
    padding: 4px 14px;
    border-radius: 12px;
    font-size: 11px;
}
QLabel#SenderChipRunning {
    background: #1a3a2a;
    color: #50fa7b;
    padding: 4px 14px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}
QLabel#SenderChipStopped {
    background: #44475a;
    color: #6272a4;
    padding: 4px 14px;
    border-radius: 12px;
    font-size: 11px;
}
QFrame#Card, QGroupBox {
    background: #21222c;
    border: 1px solid #44475a;
    border-radius: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #bd93f9;
    font-size: 12px;
}
QPushButton#PrimaryButton {
    background: #bd93f9;
    border-color: #bd93f9;
    color: #282a36;
}
QPushButton#PrimaryButton:hover {
    background: #caa9fa;
}
QPushButton#PrimaryButton:pressed {
    background: #a87df5;
}
QPushButton#SuccessButton {
    background: #50fa7b;
    border-color: #50fa7b;
    color: #282a36;
}
QPushButton#SuccessButton:hover {
    background: #6bff91;
}
QPushButton#SuccessButton:pressed {
    background: #3de068;
}
QPushButton#DangerButton {
    background: #ff5555;
    border-color: #ff5555;
    color: #282a36;
}
QPushButton#DangerButton:hover {
    background: #ff6e6e;
}
QPushButton#DangerButton:pressed {
    background: #e04040;
}

QLabel#GlobalStateRunning {
    background: #1a3a2a;
    color: #50fa7b;
    padding: 4px 14px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
}

QLabel#GlobalStateStopped {
    background: #3d1f1f;
    color: #ff5555;
    padding: 4px 14px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
}

QLineEdit, QSpinBox, QComboBox {
    padding: 4px 8px;
    min-height: 28px;
    max-height: 28px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #bd93f9;
}

QComboBox::drop-down {
    border: 0px;
}

QCheckBox::indicator:checked {
    background: #bd93f9;
    border-color: #bd93f9;
}

QLabel#FormLabel {
    color: #6272a4;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #44475a;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #6272a4;
}

QFrame#StreamCard {
    background: #282a36;
    border: 1px solid #44475a;
}
QFrame#StreamCard:hover {
    border-color: #6272a4;
}
QFrame#StreamCardRunning {
    background: #282a36;
    border: 1px solid #50fa7b;
}
QLabel#StreamName {
    color: #f8f8f2;
}
QLabel#StatusDotRunning {
    color: #50fa7b;
}
QLabel#StatusDotStopped {
    color: #44475a;
}
QPushButton#CardDeleteBtn {
    color: #6272a4;
}
QPushButton#CardDeleteBtn:hover {
    background: #3d1f1f;
    color: #ff5555;
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
        self.resize(1100, 700)
        self.setMinimumSize(960, 620)

        self.config = core.load_config()
        self.displays = []
        self.sender_displays = []
        self.is_running = False
        self.sender_is_running = False

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
        subtitle = QLabel("Routing & émission SRT vers écrans Windows")
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
        self.displays_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.displays_list.setMaximumHeight(140)
        displays_layout.addWidget(self.displays_list)

        # ── Preferences group ──
        prefs_group = QGroupBox("⚙  Préférences")
        prefs_layout = QVBoxLayout(prefs_group)
        self.exclude_primary = QCheckBox("Exclure l'écran principal")
        self.exclude_primary.setChecked(bool(self.config.get("excludePrimaryDisplay", True)))
        self.exclude_primary.stateChanged.connect(self.on_exclude_primary_changed)
        prefs_layout.addWidget(self.exclude_primary)

        # ── Sender group ──
        sender_group = QGroupBox("📡  Émission SRT")
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
        sender_row2.addWidget(_form_label("Destination"))
        self.sender_host_edit = QLineEdit()
        self.sender_host_edit.setFixedHeight(28)
        self.sender_host_edit.setPlaceholderText("ex: 192.168.1.100")
        self.sender_host_edit.editingFinished.connect(self.on_sender_changed)
        sender_row2.addWidget(self.sender_host_edit, stretch=1)
        port_label = QLabel(":")
        port_label.setFixedWidth(8)
        port_label.setAlignment(Qt.AlignCenter)
        sender_row2.addWidget(port_label)
        self.sender_port_spin = QSpinBox()
        self.sender_port_spin.setRange(1, 65535)
        self.sender_port_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.sender_port_spin.setFixedHeight(28)
        self.sender_port_spin.setFixedWidth(70)
        self.sender_port_spin.valueChanged.connect(self.on_sender_changed)
        sender_row2.addWidget(self.sender_port_spin)
        sender_layout.addLayout(sender_row2)

        sender_row3 = QHBoxLayout()
        sender_row3.setSpacing(8)
        sender_row3.addWidget(_form_label("Latence"))
        self.sender_latency_spin = QSpinBox()
        self.sender_latency_spin.setRange(0, 5000)
        self.sender_latency_spin.setSuffix(" ms")
        self.sender_latency_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.sender_latency_spin.setFixedHeight(28)
        self.sender_latency_spin.valueChanged.connect(self.on_sender_changed)
        sender_row3.addWidget(self.sender_latency_spin, stretch=1)
        fps_label = QLabel("FPS")
        fps_label.setObjectName("FormLabel")
        fps_label.setFixedWidth(30)
        fps_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        sender_row3.addWidget(fps_label)
        self.sender_fps_spin = QSpinBox()
        self.sender_fps_spin.setRange(1, 60)
        self.sender_fps_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.sender_fps_spin.setFixedHeight(28)
        self.sender_fps_spin.setFixedWidth(50)
        self.sender_fps_spin.valueChanged.connect(self.on_sender_changed)
        sender_row3.addWidget(self.sender_fps_spin)
        sender_layout.addLayout(sender_row3)

        sender_row4 = QHBoxLayout()
        sender_row4.setSpacing(8)
        sender_row4.addWidget(_form_label("Débit"))
        self.sender_bitrate_spin = QSpinBox()
        self.sender_bitrate_spin.setRange(200, 50000)
        self.sender_bitrate_spin.setSingleStep(250)
        self.sender_bitrate_spin.setSuffix(" kbps")
        self.sender_bitrate_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.sender_bitrate_spin.setFixedHeight(28)
        self.sender_bitrate_spin.valueChanged.connect(self.on_sender_changed)
        sender_row4.addWidget(self.sender_bitrate_spin, stretch=1)
        sender_layout.addLayout(sender_row4)

        sender_row4b = QHBoxLayout()
        sender_row4b.setSpacing(10)
        sender_row4b.addWidget(_form_label("Audio"))
        self.sender_audio_chk = QCheckBox("Système")
        self.sender_audio_chk.setToolTip("Inclure l'audio système dans l'émission")
        self.sender_audio_chk.stateChanged.connect(self.on_sender_changed)
        sender_row4b.addWidget(self.sender_audio_chk, stretch=1)
        sender_layout.addLayout(sender_row4b)

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

        left_scroll.setMinimumWidth(310)
        left_scroll.setMaximumWidth(340)
        streams_panel.setMinimumWidth(500)
        splitter.setSizes([320, 760])

        self.refresh_displays()
        self.reload_table()
        self.reload_sender_section()

        self.timer.start(1000)

    def on_exclude_primary_changed(self):
        self.config["excludePrimaryDisplay"] = bool(self.exclude_primary.isChecked())
        self.schedule_save()
        self.refresh_displays()
        self.reload_table()

    def refresh_displays(self):
        exclude = bool(self.config.get("excludePrimaryDisplay", True))
        self.displays = core.get_displays(exclude_primary=exclude)
        self.sender_displays = core.get_displays(exclude_primary=False)
        self.render_displays()
        self.reload_sender_section()
        self.update_header_chips()

    def reload_sender_section(self):
        sender = self.config.get("sender", {})
        current_display_id = str(sender.get("displayId") or "")

        self.sender_display_combo.blockSignals(True)
        self.sender_host_edit.blockSignals(True)
        self.sender_port_spin.blockSignals(True)
        self.sender_latency_spin.blockSignals(True)
        self.sender_fps_spin.blockSignals(True)
        self.sender_bitrate_spin.blockSignals(True)
        self.sender_audio_chk.blockSignals(True)
        try:
            self.sender_display_combo.clear()
            self.sender_display_combo.addItem("— Sélectionner —", "")
            for d in self.sender_displays:
                self.sender_display_combo.addItem(d["name"], str(d["id"]))
            idx = self.sender_display_combo.findData(current_display_id)
            if idx >= 0:
                self.sender_display_combo.setCurrentIndex(idx)

            self.sender_host_edit.setText(str(sender.get("host") or "127.0.0.1"))
            try:
                self.sender_port_spin.setValue(int(sender.get("port") or 10000))
            except Exception:
                self.sender_port_spin.setValue(10000)
            try:
                self.sender_latency_spin.setValue(int(sender.get("latency") or 120))
            except Exception:
                self.sender_latency_spin.setValue(120)
            try:
                self.sender_fps_spin.setValue(int(sender.get("fps") or 30))
            except Exception:
                self.sender_fps_spin.setValue(30)
            try:
                self.sender_bitrate_spin.setValue(int(sender.get("bitrateK") or 4000))
            except Exception:
                self.sender_bitrate_spin.setValue(4000)

            self.sender_audio_chk.setChecked(bool(sender.get("includeSystemAudio", False)))
        finally:
            self.sender_display_combo.blockSignals(False)
            self.sender_host_edit.blockSignals(False)
            self.sender_port_spin.blockSignals(False)
            self.sender_latency_spin.blockSignals(False)
            self.sender_fps_spin.blockSignals(False)
            self.sender_bitrate_spin.blockSignals(False)
            self.sender_audio_chk.blockSignals(False)

        self.refresh_sender_status()

    def on_sender_changed(self, *_args):
        sender = self.config.setdefault("sender", {})
        sender["displayId"] = str(self.sender_display_combo.currentData() or "")
        sender["host"] = self.sender_host_edit.text().strip() or "127.0.0.1"
        sender["port"] = int(self.sender_port_spin.value())
        sender["latency"] = int(self.sender_latency_spin.value())
        sender["fps"] = int(self.sender_fps_spin.value())
        sender["bitrateK"] = int(self.sender_bitrate_spin.value())
        sender["includeSystemAudio"] = bool(self.sender_audio_chk.isChecked())
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
            self.sender_chip.setText("📡 Émission: ▶")
            self.sender_chip.setObjectName("SenderChipRunning")
        else:
            self.sender_status_label.setText("⏹ arrêté")
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
            QMessageBox.warning(self, "Émission SRT", "Sélectionne un écran à émettre.")
            return

        display = next((d for d in self.sender_displays if str(d.get("id")) == display_id), None)
        if not display:
            QMessageBox.warning(self, "Émission SRT", "L'écran sélectionné n'est plus disponible.")
            return

        host = str(sender.get("host") or "127.0.0.1")
        port = int(sender.get("port") or 10000)
        latency = int(sender.get("latency") or 120)
        fps = int(sender.get("fps") or 30)
        bitrate_k = int(sender.get("bitrateK") or 4000)
        include_system_audio = bool(sender.get("includeSystemAudio", False))
        result = core.sender_manager.start(
            display,
            host,
            port,
            latency_ms=latency,
            fps=fps,
            bitrate_k=bitrate_k,
            include_system_audio=include_system_audio,
        )
        if not result.ok:
            QMessageBox.warning(
                self,
                "Émission SRT",
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

        delete_btn = QPushButton("✕")
        delete_btn.setObjectName("CardDeleteBtn")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setToolTip("Supprimer ce flux")
        delete_btn.clicked.connect(lambda checked=False, r=row: self._delete_stream(r))
        top_row.addWidget(delete_btn)

        card_layout.addLayout(top_row)

        # ── Row 2: port + latency + screen ──
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        port_lbl = QLabel("Port")
        port_lbl.setObjectName("FormLabel")
        port_lbl.setFixedWidth(30)
        port_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bottom_row.addWidget(port_lbl)

        port_spin = QSpinBox()
        port_spin.setRange(1, 65535)
        port_spin.setValue(int(stream.get("port", 9000)))
        port_spin.setButtonSymbols(QSpinBox.NoButtons)
        port_spin.setFixedHeight(28)
        port_spin.setFixedWidth(70)
        port_spin.valueChanged.connect(lambda v, r=row: self._on_card_changed(r))
        bottom_row.addWidget(port_spin)

        lat_lbl = QLabel("Latence")
        lat_lbl.setObjectName("FormLabel")
        lat_lbl.setFixedWidth(48)
        lat_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bottom_row.addWidget(lat_lbl)

        latency_spin = QSpinBox()
        latency_spin.setRange(0, 5000)
        latency_spin.setValue(int(stream.get("latency", 120)))
        latency_spin.setSuffix(" ms")
        latency_spin.setButtonSymbols(QSpinBox.NoButtons)
        latency_spin.setFixedHeight(28)
        latency_spin.setFixedWidth(80)
        latency_spin.valueChanged.connect(lambda v, r=row: self._on_card_changed(r))
        bottom_row.addWidget(latency_spin)

        mute_chk = QCheckBox("Muet")
        mute_chk.setChecked(bool(stream.get("muteAudio")))
        mute_chk.setToolTip("Couper l'audio de ce flux")
        mute_chk.stateChanged.connect(lambda _v, r=row: self._on_card_changed(r))
        bottom_row.addWidget(mute_chk)

        screen_lbl = QLabel("Écran")
        screen_lbl.setObjectName("FormLabel")
        screen_lbl.setFixedWidth(38)
        screen_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bottom_row.addWidget(screen_lbl)

        display_combo = QComboBox()
        display_combo.addItem("— Non assigné —", "")
        for d in self.displays:
            display_combo.addItem(d["name"], str(d["id"]))
        display_combo.setFixedHeight(28)

        current_display_id = self.config.get("mapping", {}).get(stream_id)
        if current_display_id is not None and str(current_display_id) in display_ids:
            idx = display_combo.findData(str(current_display_id))
            if idx >= 0:
                display_combo.setCurrentIndex(idx)
        elif current_display_id is not None:
            self.config.get("mapping", {}).pop(stream_id, None)

        display_combo.currentIndexChanged.connect(lambda v, r=row: self._on_card_changed(r))
        bottom_row.addWidget(display_combo, stretch=1)

        card_layout.addLayout(bottom_row)

        return {
            "card": card,
            "name_edit": name_edit,
            "port_spin": port_spin,
            "latency_spin": latency_spin,
            "mute_chk": mute_chk,
            "display_combo": display_combo,
            "status_dot": status_dot,
            "status_label": status_label,
            "stream_id": stream_id,
        }

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
        core.sender_manager.stop()
        self.refresh_status()
        self.refresh_sender_status()
        self.update_toggle_button(False)

    def toggle_start_stop(self):
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
        self.btn_toggle.style().unpolish(self.btn_toggle)
        self.btn_toggle.style().polish(self.btn_toggle)

    def refresh_status(self):
        status = core.player_manager.status()
        streams = self.config.get("streams", [])

        for row, stream in enumerate(streams):
            if row >= len(self.stream_cards):
                break
            stream_id = str(stream.get("id"))
            running = status.get(stream_id, False)
            card_info = self.stream_cards[row]

            if running:
                card_info["status_dot"].setObjectName("StatusDotRunning")
                card_info["status_label"].setText("en cours")
                card_info["status_label"].setStyleSheet("color: #50fa7b; font-weight: 600;")
                card_info["card"].setObjectName("StreamCardRunning")
            else:
                card_info["status_dot"].setObjectName("StatusDotStopped")
                card_info["status_label"].setText("arrêté")
                card_info["status_label"].setStyleSheet("color: #64748b;")
                card_info["card"].setObjectName("StreamCard")

            card_info["status_dot"].style().unpolish(card_info["status_dot"])
            card_info["status_dot"].style().polish(card_info["status_dot"])
            card_info["card"].style().unpolish(card_info["card"])
            card_info["card"].style().polish(card_info["card"])

        self.update_header_chips(status)
        self.update_toggle_button(any(status.values()))
        self.refresh_sender_status()

    def add_stream(self):
        now = int(time.time() * 1000)
        next_index = len(self.config.get("streams", [])) + 1
        stream_id = f"stream-{now}"
        self.config.setdefault("streams", []).append(
            {"id": stream_id, "name": f"Flux {next_index}", "port": 9000 + next_index, "latency": 120}
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
            self.displays_list.addItem(item)

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
        core.player_manager.stop_all()
        core.sender_manager.stop()
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
