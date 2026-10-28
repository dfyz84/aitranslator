$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Virtual environment was not found. Create it first:" -ForegroundColor Yellow
    Write-Host "  py -3.12 -m venv .venv"
    Write-Host "  .\.venv\Scripts\python.exe -m pip install poetry"
    Write-Host "  .\.venv\Scripts\poetry.exe install"
    exit 1
}

Write-Host "Starting AI Translator web app..." -ForegroundColor Green
Write-Host "Open: http://127.0.0.1:8000/ui" -ForegroundColor Cyan
& $python -m src.scripts.server --host 127.0.0.1 --port 8000
