$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$required = @(
    'library\vxlapi64.dll',
    'library\windows\x86_64\tosun\libTSCAN.dll',
    'library\windows\x86_64\tosun\libTSH.dll',
    'library\windows\x86_64\zlgcan.dll',
    'library\windows\x86_64\kerneldlls\USBCANFD.dll',
    'library\windows\x86_64\kerneldlls\USBCANFD800U.dll',
    'profile\S20\vehicleinfo.json',
    'profile\S20\M18_Upper_Interface_241113.dbc',
    'profile\S20\ObstacleTrack_M20251104.dbc',
    'profile\S20\S20_Upper_CAN_UC_v1_20261117.dbc'
)
foreach ($relativePath in $required) {
    $runtimeFile = Join-Path $projectRoot $relativePath
    if (-not (Test-Path -LiteralPath $runtimeFile -PathType Leaf)) {
        throw "Required runtime asset not found: $runtimeFile"
    }
}
Write-Host 'Windows x64 runtime assets are complete.'
