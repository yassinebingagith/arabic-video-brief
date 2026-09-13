param(
    [string]$Target = "gemini",
    [string]$CustomDestination = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ResolvedProject = (Resolve-Path -LiteralPath $ProjectRoot).Path

if ($CustomDestination) {
    $Destination = $CustomDestination
} elseif ($Target -eq "gemini" -or $Target -eq "antigravity") {
    $Destination = [System.IO.Path]::Combine($env:USERPROFILE, ".gemini", "config", "skills", "arabic-video-brief")
} else {
    $Destination = [System.IO.Path]::Combine($env:USERPROFILE, ".codex", "skills", "arabic-video-brief")
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Destination "scripts") | Out-Null
Copy-Item -LiteralPath (Join-Path $ProjectRoot "SKILL.md") -Destination $Destination -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "agents") -Destination $Destination -Recurse -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "references") -Destination $Destination -Recurse -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "scripts\avbrief.py") -Destination (Join-Path $Destination "scripts\avbrief.py") -Force
if (Test-Path -LiteralPath (Join-Path $ProjectRoot "assets")) {
    $destAssets = Join-Path $Destination "assets"
    New-Item -ItemType Directory -Force -Path $destAssets | Out-Null
    Copy-Item -LiteralPath (Join-Path $ProjectRoot "assets\NotoSansArabic-SemiBold.ttf") -Destination $destAssets -Force
    if (Test-Path -LiteralPath (Join-Path $ProjectRoot "assets\brand")) {
        Copy-Item -LiteralPath (Join-Path $ProjectRoot "assets\brand") -Destination $destAssets -Recurse -Force
    }
    if (Test-Path -LiteralPath (Join-Path $ProjectRoot "assets\music")) {
        Copy-Item -LiteralPath (Join-Path $ProjectRoot "assets\music") -Destination $destAssets -Recurse -Force
    }
}
Write-Output "Installed Arabic Video Brief skill from $ResolvedProject to $Destination"
