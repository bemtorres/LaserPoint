@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  LaserPoint - Instalacion (Win)
echo ============================================

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No se encontro Python. Instala Python 3.10+ desde python.org
  pause
  exit /b 1
)

if not exist ".venv" (
  echo Creando entorno virtual...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
  )
)

echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Fallo la instalacion de dependencias.
  pause
  exit /b 1
)

echo Generando icono...
".venv\Scripts\python.exe" tools\make_icon.py

echo Creando accesos directos...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\make_shortcut.ps1"
if errorlevel 1 (
  echo [AVISO] No se pudieron crear los accesos directos.
)

echo.
echo Instalacion completada.
echo   - Arranque rapido : start.bat
echo   - Acceso directo  : Escritorio y Menu Inicio "LaserPoint"
echo   - Atajo por defecto: Ctrl+Alt+L
echo.
pause
