$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
# Load environment variables from .env
Get-Content (Join-Path $PSScriptRoot ".env") | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') { $key=$matches[1]; $value=$matches[2]; Set-Item -Path ("Env:" + $key) -Value $value }
}
& $python app.py
