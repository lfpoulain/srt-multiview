import os
import shutil
import sys
from pathlib import Path


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


ROOT_DIR = _runtime_root_dir()
APP_DIR = _runtime_app_dir()
BIN_DIR = ROOT_DIR / "bin"
IMG_DIR = ROOT_DIR / "img"


def _resolve_binary_path(filename: str) -> Path:
    """Locate an executable, preferring the project-local ``bin/`` folder.

    Order: ``BIN_DIR`` -> ``APP_DIR/bin`` -> ``shutil.which`` (system PATH).
    The bundled binary is preferred so a custom (e.g. OMT-enabled) FFmpeg
    shipped with the app is never shadowed by a system install.
    """
    for candidate in (BIN_DIR / filename, APP_DIR / "bin" / filename):
        if candidate.exists():
            return candidate

    names = [filename]
    if filename.lower().endswith(".exe"):
        names.append(filename[:-4])
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return Path(resolved)

    return BIN_DIR / filename


def _user_config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "srt-multiview"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "srt-multiview"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "srt-multiview"


CONFIG_DIR = _user_config_dir()
CONFIG_PATH = CONFIG_DIR / "config.json"
FFPLAY_PATH = _resolve_binary_path("ffplay.exe" if sys.platform == "win32" else "ffplay")
FFMPEG_PATH = _resolve_binary_path("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")

APP_ICON_ICO_PATH = IMG_DIR / "icon.ico"
APP_ICON_PNG_PATH = IMG_DIR / "icon.png"
