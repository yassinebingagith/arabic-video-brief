param(
    [string]$PythonPath,
    [switch]$WithPublisher,
    [switch]$WithTests,
    [switch]$SkipRenderer
)
$ErrorActionPreference = 'Stop'
$setupArguments = @((Join-Path $PSScriptRoot 'setup.py'))
if($WithPublisher){$setupArguments += '--with-publisher'}
if($WithTests){$setupArguments += '--with-tests'}
if($SkipRenderer){$setupArguments += '--skip-renderer'}
if(-not $PythonPath){
    $candidate = Get-Command python,python3,py -ErrorAction SilentlyContinue | Select-Object -First 1
    if(-not $candidate){throw 'Install Python 3.11+ or pass -PythonPath with its executable.'}
    $PythonPath = $candidate.Source
    if($candidate.Name -eq 'py.exe'){$setupArguments = @('-3') + $setupArguments}
}
& $PythonPath @setupArguments
if($LASTEXITCODE -ne 0){throw "Setup failed (exit $LASTEXITCODE)."}
