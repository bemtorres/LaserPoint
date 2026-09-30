$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$pyw = Join-Path $root ".venv\Scripts\pythonw.exe"
$main = Join-Path $root "main.py"
$ico = Join-Path $root "assets\icon.ico"
$workdir = $root

if (-not (Test-Path $pyw)) {
    Write-Error "No existe el entorno virtual (.venv). Ejecuta install.bat"
    exit 1
}

$WshShell = New-Object -ComObject WScript.Shell
$programs = [Environment]::GetFolderPath("Programs")
$desktop = [Environment]::GetFolderPath("Desktop")
$folder = Join-Path $programs "LaserPoint"
New-Item -ItemType Directory -Force -Path $folder | Out-Null

$targets = @(
    (Join-Path $desktop "LaserPoint.lnk"),
    (Join-Path $folder "LaserPoint.lnk")
)

foreach ($target in $targets) {
    $shortcut = $WshShell.CreateShortcut($target)
    $shortcut.TargetPath = $pyw
    $shortcut.Arguments = "`"$main`""
    $shortcut.WorkingDirectory = $workdir
    $shortcut.WindowStyle = 7
    $shortcut.Description = "LaserPoint"
    if (Test-Path $ico) {
        $shortcut.IconLocation = "$ico,0"
    }
    $shortcut.Save()
    Write-Host "acceso directo: $target"
}
