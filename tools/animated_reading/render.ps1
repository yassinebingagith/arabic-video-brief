param(
    [Parameter(Mandatory=$true)][string]$Project,
    [ValidateSet('draft','standard','high')][string]$Quality='high'
)
$ErrorActionPreference='Stop'
$node = Get-Command node -ErrorAction SilentlyContinue
if(-not $node){throw 'Install Node.js 22+ and run python scripts/setup.py.'}
& $node.Source (Join-Path $PSScriptRoot 'render.mjs') --project $Project --quality $Quality
if($LASTEXITCODE -ne 0){throw "Page render failed (exit $LASTEXITCODE)."}
