from pathlib import Path
import shutil
import sys


def _runtime_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _runtime_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _resolve_binary_path(filename: str) -> Path:
    which_names = [filename]
    if filename.lower().endswith(".exe"):
        which_names.append(filename[:-4])

    for which_name in which_names:
        resolved = shutil.which(which_name)
        if resolved:
            return Path(resolved)

    return BIN_DIR / filename


ROOT_DIR = _runtime_root_dir()
BIN_DIR = ROOT_DIR / "bin"
IMG_DIR = ROOT_DIR / "img"

CONFIG_PATH = Path.home() / "srt-multiview-config.json"
FFPLAY_PATH = _resolve_binary_path("ffplay.exe")
FFMPEG_PATH = _resolve_binary_path("ffmpeg.exe")

APP_ICON_ICO_PATH = IMG_DIR / "icon.ico"
APP_ICON_PNG_PATH = IMG_DIR / "icon.png"
