# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_dir = Path(globals().get("SPECPATH", ".")).resolve()

block_cipher = None

# Include resources needed at runtime
_datas = [
    (str(project_dir / "config.json"), "."),
    (str(project_dir / "img"), "img"),
    (str(project_dir / "bin"), "bin"),
]

_a = Analysis(
    ["run_app.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(_a.pure, _a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    _a.scripts,
    _a.binaries,
    _a.zipfiles,
    _a.datas,
    [],
    name="SRT-MultiView",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=str(project_dir / "img" / "icon.ico"),
)
