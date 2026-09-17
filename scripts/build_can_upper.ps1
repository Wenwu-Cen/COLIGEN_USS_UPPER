$ErrorActionPreference = 'Stop'

Set-Location (Split-Path -Parent $PSScriptRoot)

function Assert-LastExitCode {
    param([Parameter(Mandatory = $true)][string]$Command)
    if ($LASTEXITCODE -ne 0) {
        throw "$Command failed with exit code $LASTEXITCODE"
    }
}

& (Join-Path $PSScriptRoot 'prepare_zlgcan_runtime.ps1') -ProjectRoot (Get-Location).Path

uv sync
Assert-LastExitCode 'uv sync'

# Use `python -m PyInstaller` instead of the `pyinstaller` console-script
# trampoline. After the project folder is moved, uv's trampoline may still
# point at the old path and fail to canonicalize it.
uv run python -m PyInstaller --clean --noconfirm VehUpperDemo.spec
Assert-LastExitCode 'uv run python -m PyInstaller'

$exeStem = (
    uv run python -c "import sys; sys.path.insert(0, 'src'); from app_version import EXE_STEM; print(EXE_STEM)"
).Trim()
Write-Host "Build complete: dist\$exeStem.exe"
