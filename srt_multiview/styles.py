from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

import qdarktheme


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
QLabel#StatusDotStarting {
    color: #f59e0b;
}
QPushButton#CardDeleteBtn {
    color: #6272a4;
}
QPushButton#CardDeleteBtn:hover {
    background: #3d1f1f;
    color: #ff5555;
}
"""


def enable_hi_dpi() -> None:
    qdarktheme.enable_hi_dpi()


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setFont(QFont("Bahnschrift", 10))
    qdarktheme.setup_theme(
        theme="dark",
        corner_shape="rounded",
        custom_colors={"primary": "#bd93f9"},
        additional_qss=DRACULA_OVERLAY_QSS,
    )
