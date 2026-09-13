param(
    [string]$PythonPath = "C:\Users\User\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Python 3.11+ was not found. Pass -PythonPath with an installed Python executable."
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    & $PythonPath -m venv (Join-Path $ProjectRoot ".venv")
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e "$ProjectRoot[vision,test]"

$EnvFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot ".env.example") -Destination $EnvFile
}

& $VenvPython (Join-Path $ProjectRoot "scripts\avbrief.py") doctor
