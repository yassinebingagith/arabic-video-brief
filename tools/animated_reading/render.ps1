param(
    [Parameter(Mandatory=$true)][string]$Project,
    [ValidateSet('draft','standard','high')][string]$Quality='high'
)
$ErrorActionPreference='Stop'
$pageRuntime=Get-Content -LiteralPath 'F:/hyperframes-v3/config/local-runtime.json' -Raw | ConvertFrom-Json
$env:CHROME_BIN=$pageRuntime.CHROME_BIN
$env:PUPPETEER_EXECUTABLE_PATH=$pageRuntime.CHROME_BIN
$env:FFMPEG_PATH=$pageRuntime.FFMPEG_BIN
$env:FFMPEG_BIN=$pageRuntime.FFMPEG_BIN
$env:PATH=(Split-Path $pageRuntime.FFMPEG_BIN)+';'+$env:PATH
$pageProject=(Resolve-Path -LiteralPath $Project).Path
$pageCli='F:/hyperframes-v3/renderers/hyperframes/node_modules/hyperframes/bin/hyperframes.mjs'
& $pageRuntime.NODE_BIN $pageCli lint $pageProject --json
if($LASTEXITCODE -ne 0){throw 'Page composition lint failed.'}
& $pageRuntime.NODE_BIN $pageCli render $pageProject -o (Join-Path (Split-Path $pageProject) 'reading-pages.mp4') --fps 30 --quality $Quality --workers 1 --low-memory-mode --strict --no-best-effort
if($LASTEXITCODE -ne 0){throw 'Page render failed.'}
