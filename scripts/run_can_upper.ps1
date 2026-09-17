$ErrorActionPreference = 'Stop'

Set-Location (Split-Path -Parent $PSScriptRoot)

& (Join-Path $PSScriptRoot 'prepare_zlgcan_runtime.ps1') -ProjectRoot (Get-Location).Path

uv run python src/VehUpperDemo_CAN.py
