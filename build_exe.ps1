# Build SRT-MultiView Windows executable (PyInstaller)
# Usage (PowerShell): .\build_exe.ps1

$ErrorActionPreference = "Stop"

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    throw "Python venv introuvable: $py. Crée/active le venv puis relance."
}

& $py -m pip install --upgrade pip
& $py -m pip install pyinstaller

# Clean previous builds
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

& $py -m PyInstaller --noconfirm .\srt_multiview.spec

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller a échoué (code=$LASTEXITCODE)."
}

Write-Host "Build terminé. Voir dist\SRT-MultiView\SRT-MultiView.exe"
