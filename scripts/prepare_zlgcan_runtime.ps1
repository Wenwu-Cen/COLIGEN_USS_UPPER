param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

$source = Join-Path $ProjectRoot 'library\zlgcan.dll'
$libraryRoot = Join-Path $ProjectRoot 'library'
$targetDirectory = Join-Path $ProjectRoot 'library\windows\x86_64'
$target = Join-Path $targetDirectory 'zlgcan.dll'

if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "ZLG CAN runtime not found: $source"
}

New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null

$copyRequired = -not (Test-Path -LiteralPath $target -PathType Leaf)
if (-not $copyRequired) {
    $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash
    $targetHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash
    $copyRequired = $sourceHash -ne $targetHash
}

if ($copyRequired) {
    Copy-Item -Force -LiteralPath $source -Destination $target
}

$requiredRuntimeFiles = @(
    (Join-Path $libraryRoot 'bitrate.cfg.yaml'),
    (Join-Path $targetDirectory 'kerneldlls\dll_cfg.ini'),
    (Join-Path $targetDirectory 'kerneldlls\USBCANFD.dll'),
    (Join-Path $targetDirectory 'kerneldlls\devices_property\usbcanfd-200u.xml')
)

$missingRuntimeFiles = @(
    $requiredRuntimeFiles | Where-Object {
        -not (Test-Path -LiteralPath $_ -PathType Leaf)
    }
)
if ($missingRuntimeFiles.Count -gt 0) {
    $missingList = $missingRuntimeFiles -join [Environment]::NewLine
    throw "ZLG CAN companion runtime is incomplete:$([Environment]::NewLine)$missingList"
}

Write-Host "ZLG CAN runtime ready: $libraryRoot"
