$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$required = @(
    'library\vxlapi64.dll',
    'library\windows\x86_64\zlgcan.dll',
    'library\windows\x86_64\kerneldlls\USBCANFD.dll',
    'library\windows\x86_64\kerneldlls\USBCANFD800U.dll',
    'assets\dbc\M18_Upper_Interface_241113.dbc',
    'assets\dbc\ObstacleTrack_M20251104.dbc'
)
foreach ($relativePath in $required) {
    $runtimeFile = Join-Path $projectRoot $relativePath
    if (-not (Test-Path -LiteralPath $runtimeFile -PathType Leaf)) {
        throw "Required runtime asset not found: $runtimeFile"
    }
}
Write-Host 'Windows x64 runtime assets are complete.'
