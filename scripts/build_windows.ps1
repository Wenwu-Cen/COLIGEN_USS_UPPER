$ErrorActionPreference = 'Stop'

Set-Location (Split-Path -Parent $PSScriptRoot)

function Assert-LastExitCode {
    param([Parameter(Mandatory = $true)][string]$Command)
    if ($LASTEXITCODE -ne 0) {
        throw "$Command failed with exit code $LASTEXITCODE"
    }
}

& (Join-Path $PSScriptRoot 'check_runtime.ps1')

$vectorDllName = 'vxlapi64.dll'
$vectorDll = Join-Path (Get-Location) "library\$vectorDllName"
if (-not (Test-Path -LiteralPath $vectorDll -PathType Leaf)) {
    throw "CANoe/Vector runtime not found: $vectorDll"
}

uv sync --locked
Assert-LastExitCode 'uv sync --locked'

# Use `python -m PyInstaller` instead of the `pyinstaller` console-script
# trampoline. After the project folder is moved, uv's trampoline may still
# point at the old path and fail to canonicalize it.
uv run python -m PyInstaller --clean --noconfirm --workpath build/windows/work --distpath build/windows/dist scripts/pyinstaller/windows.spec
Assert-LastExitCode 'uv run python -m PyInstaller'

$exeStem = (
    uv run python -c "import sys; sys.path.insert(0, 'src'); from app_version import EXE_STEM; print(EXE_STEM)"
).Trim()
$package = Join-Path 'build/windows/dist' $exeStem
$settingsDirectory = Join-Path $package 'config'
New-Item -ItemType Directory -Path $settingsDirectory -Force | Out-Null
Copy-Item -LiteralPath 'config/viewer.toml' -Destination $settingsDirectory
Copy-Item -LiteralPath 'profile' -Destination $package -Recurse

$workerName = 'dataReplay_main.exe'
$workerManifests = @{
    S20 = 'replay_s20_build_manifest.json'
    D4M3 = 'build_manifest.json'
}
foreach ($project in $workerManifests.Keys) {
    $destination = Join-Path $package "profile/$project"
    $source = Join-Path 'build' "$($project.ToLowerInvariant())-stream/bin"
    $worker = Join-Path $source $workerName
    if ((Test-Path -LiteralPath (Join-Path $destination $workerName) -PathType Leaf) -or
        -not (Test-Path -LiteralPath $worker -PathType Leaf)) {
        continue
    }
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Copy-Item -LiteralPath $worker -Destination $destination
    $manifest = Join-Path $source $workerManifests[$project]
    if (Test-Path -LiteralPath $manifest -PathType Leaf) {
        Copy-Item -LiteralPath $manifest -Destination $destination
    }
}

New-Item -ItemType Directory -Path 'dist' -Force | Out-Null
$archive = Join-Path 'dist' "$exeStem-Windows-Portable.zip"
Compress-Archive -LiteralPath $package -DestinationPath $archive -Force
Write-Host "Build complete: $archive"
