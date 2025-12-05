Param(
    [string]$PyInstaller = "pyinstaller"
)

$ErrorActionPreference = "Stop"

function Resolve-Root {
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    return (Resolve-Path (Join-Path $scriptPath "..")).Path
}

$root = Resolve-Root
$backendDist = Join-Path $root "desktop/resources/backend"
$desktopDir = Join-Path $root "desktop"
$frontendDir = Join-Path $root "frontend"

Write-Host "==> Building backend executable with PyInstaller"
if (-not (Get-Command $PyInstaller -ErrorAction SilentlyContinue)) {
    throw "PyInstaller no está instalado. Ejecuta 'pip install pyinstaller' o invoca el script con -PyInstaller <ruta>."
}

New-Item -ItemType Directory -Force -Path $backendDist | Out-Null
& $PyInstaller "$root/backend/desktop_main.py" `
    --name criptohacienda-backend `
    --onefile `
    --distpath $backendDist `
    --workpath "$root/backend/.pyinstaller-build" `
    --clean

Write-Host "==> Instalando dependencias de Electron"
Push-Location $desktopDir
npm install

Write-Host "==> Reempaquetando frontend"
npm run sync:frontend

Write-Host "==> Construyendo instalador de Windows (.exe)"
npm run build:windows
Pop-Location

Write-Host "Instalador generado en desktop/dist/"
