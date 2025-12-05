#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIST_DIR="$ROOT_DIR/desktop/resources/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
DESKTOP_DIR="$ROOT_DIR/desktop"
PYINSTALLER_BIN="${PYINSTALLER:-pyinstaller}"

echo "==> Building backend binary with PyInstaller"
if ! command -v "$PYINSTALLER_BIN" >/dev/null 2>&1; then
  echo "PyInstaller no está instalado. Instálalo con 'pip install pyinstaller' o define PYINSTALLER=/ruta/pyinstaller"
  exit 1
fi

mkdir -p "$BACKEND_DIST_DIR"
"$PYINSTALLER_BIN" "$ROOT_DIR/backend/desktop_main.py" \
  --name criptohacienda-backend \
  --onefile \
  --distpath "$BACKEND_DIST_DIR" \
  --workpath "$ROOT_DIR/backend/.pyinstaller-build" \
  --clean

echo "==> Installing/Updating desktop dependencies"
pushd "$DESKTOP_DIR" >/dev/null
npm install

echo "==> Bundling frontend assets"
npm run sync:frontend

echo "==> Building Linux AppImage"
npm run build:linux
popd >/dev/null

echo "AppImage generado en desktop/dist/"
