#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "==========================================="
echo " LaserPoint - Instalacion"
echo "==========================================="

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] No se encontro python3. Instala Python 3.10+"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creando entorno virtual..."
  "$PYTHON_BIN" -m venv .venv
fi

echo "Instalando dependencias..."
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/python -m pip install -r requirements.txt

echo "Generando icono..."
.venv/bin/python tools/make_icon.py || echo "[AVISO] icono no generado"

if [ "$(uname)" = "Darwin" ]; then
  APP="LaserPoint.app"
  mkdir -p "$APP/Contents/MacOS"
  cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>LaserPoint</string>
  <key>CFBundleDisplayName</key>
  <string>LaserPoint</string>
  <key>CFBundleIdentifier</key>
  <string>com.laserpoint</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleVersion</key>
  <string>1.0.0</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0.0</string>
  <key>CFBundleExecutable</key>
  <string>LaserPoint</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>LSUIElement</key>
  <true/>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
</dict>
</plist>
PLIST
  cat > "$APP/Contents/MacOS/LaserPoint" <<'LAUNCH'
#!/bin/bash
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
exec "$ROOT/.venv/bin/python" "$ROOT/main.py"
LAUNCH
  chmod +x "$APP/Contents/MacOS/LaserPoint"
  echo "Aplicacion creada: $APP"
  echo "[NOTA] En macOS concede permisos de Accesibilidad a Terminal/Python"
  echo "       para que el atajo global funcione."
else
  mkdir -p "$HOME/.local/share/applications"
  cat > "$HOME/.local/share/applications/laserpoint.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=LaserPoint
Exec=$PWD/.venv/bin/python $PWD/main.py
Terminal=false
Categories=Utility;
DESKTOP
  echo "Lanzador de escritorio creado."
fi

echo
echo "Instalacion completada. Ejecuta ./start.sh"
