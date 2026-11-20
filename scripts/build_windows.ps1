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
uv run python -m PyInstaller --clean --noconfirm --workpath build/windows scripts/pyinstaller/windows.spec
Assert-LastExitCode 'uv run python -m PyInstaller'

$exeStem = (
    uv run python -c "import sys; sys.path.insert(0, 'src'); from app_version import EXE_STEM; print(EXE_STEM)"
).Trim()
Write-Host "Build complete: dist\$exeStem.exe"
