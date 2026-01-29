from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BIN_DIR = ROOT_DIR / "bin"
IMG_DIR = ROOT_DIR / "img"

CONFIG_PATH = ROOT_DIR / "config.json"
FFPLAY_PATH = BIN_DIR / "ffplay.exe"

APP_ICON_ICO_PATH = IMG_DIR / "icon.ico"
APP_ICON_PNG_PATH = IMG_DIR / "icon.png"
