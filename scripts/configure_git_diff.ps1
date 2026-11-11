param(
    [string]$PythonExecutable = (Get-Command python -ErrorAction Stop).Source
)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$helper = Join-Path $HOME "bin\git_decrypt_textconv.py"
New-Item -ItemType Directory -Path (Split-Path -Parent $helper) -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "git_decrypt_textconv.py") -Destination $helper -Force
$attributes = Join-Path $HOME ".gitattributes"
if (-not (Test-Path -LiteralPath $attributes)) {
    New-Item -ItemType File -Path $attributes | Out-Null
}
$existing = @(Get-Content -LiteralPath $attributes)
foreach ($pattern in @("*.c", "*.h", "*.py", "*.pyi", "*.spec", "*.toml", "*.ps1", "*.sh")) {
    $line = "$pattern diff=decrypt"
    if ($existing -notcontains $line) {
        Add-Content -LiteralPath $attributes -Value $line -Encoding UTF8
    }
}
$driver = '"{0}" "{1}"' -f $PythonExecutable.Replace('\', '/'), $helper.Replace('\', '/')
& git config --global core.attributesFile "~/.gitattributes"
if ($LASTEXITCODE) { throw "Cannot set attributes file" }
& git config --global diff.decrypt.textconv $driver
if ($LASTEXITCODE) { throw "Cannot set textconv" }
& git config --global diff.decrypt.cachetextconv false
if ($LASTEXITCODE) { throw "Cannot disable stale conversion cache" }
Push-Location $projectRoot
try {
    $content = & git show --textconv HEAD:src/app_version.py
    if ($LASTEXITCODE -or ($content -join "`n").Contains("%TSD-Header-")) {
        throw "Plaintext unavailable. Use a Python executable authorized by the installed encryption client."
    }
    Write-Host "Git / VS Code textconv verification passed."
} finally {
    Pop-Location
}
