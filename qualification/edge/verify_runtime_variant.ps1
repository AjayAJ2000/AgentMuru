[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Manifest,
    [Parameter(Mandatory = $true)][string]$VariantID,
    [switch]$ExecuteVersion
)

$ErrorActionPreference = "Stop"
$manifestPath = (Resolve-Path $Manifest).Path
$value = Get-Content -Raw -Encoding UTF8 $manifestPath | ConvertFrom-Json
$variant = $value.variants | Where-Object { $_.id -eq $VariantID } | Select-Object -First 1
if (-not $variant) { throw "runtime variant '$VariantID' is absent from the manifest" }
$binary = Join-Path (Split-Path -Parent $manifestPath) $variant.filename
if (-not (Test-Path -LiteralPath $binary)) { throw "runtime binary is missing: $binary" }
$actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $binary).Hash.ToLowerInvariant()
if ($actual -ne $variant.sha256) { throw "runtime digest mismatch; binary was not executed" }
if ((Get-Item -LiteralPath $binary).Length -ne $variant.size_bytes) { throw "runtime size mismatch; binary was not executed" }
Write-Output "Verified $VariantID at $actual"
if ($ExecuteVersion) {
    & $binary --version
    if ($LASTEXITCODE -ne 0) { throw "verified runtime failed its version command" }
}
