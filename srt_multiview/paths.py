from pathlib import Path
import sys


def _runtime_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


ROOT_DIR = _runtime_root_dir()
BIN_DIR = ROOT_DIR / "bin"
IMG_DIR = ROOT_DIR / "img"

CONFIG_PATH = ROOT_DIR / "config.json"
FFPLAY_PATH = BIN_DIR / "ffplay.exe"

APP_ICON_ICO_PATH = IMG_DIR / "icon.ico"
APP_ICON_PNG_PATH = IMG_DIR / "icon.png"
