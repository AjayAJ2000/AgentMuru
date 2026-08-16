[CmdletBinding()]
param(
    [string]$GoExecutable = "go",
    [string]$RuntimeManifest = "",
    [string]$VariantID = "",
    [string]$ReportPath = ".tmp/qualification/model-runtime-smoke.json"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$report = if ([System.IO.Path]::IsPathRooted($ReportPath)) { $ReportPath } else { Join-Path $repositoryRoot $ReportPath }
New-Item -ItemType Directory -Force (Split-Path -Parent $report) | Out-Null
$checks = @()

Push-Location (Join-Path $repositoryRoot "edge")
try {
    & $GoExecutable test ./internal/catalog ./internal/download ./internal/inference ./internal/events -count=1
    $componentPassed = $LASTEXITCODE -eq 0
    $checks += [pscustomobject][ordered]@{ name = "fixture model runtime components"; passed = $componentPassed; detail = "signed catalog, download, supervisor, constrained decision, residency, durable events" }

    & $GoExecutable build -trimpath -o (Join-Path $repositoryRoot ".tmp/qualification/muru-smoke.exe") ./cmd/muru
    $buildPassed = $LASTEXITCODE -eq 0
    $checks += [pscustomobject][ordered]@{ name = "native binary build"; passed = $buildPassed }
} finally {
    Pop-Location
}

if ($RuntimeManifest -or $VariantID) {
    if (-not $RuntimeManifest -or -not $VariantID) { throw "RuntimeManifest and VariantID must be supplied together" }
    & (Join-Path $PSScriptRoot "verify_runtime_variant.ps1") -Manifest $RuntimeManifest -VariantID $VariantID
    $checks += [pscustomobject][ordered]@{ name = "runtime archive digest"; passed = ($LASTEXITCODE -eq 0); detail = $VariantID }
}

$passed = ($checks | Where-Object { -not $_.passed }).Count -eq 0
[ordered]@{
    schema_version = "qualification.agentmuru.dev/edge-runtime/v1"
    generated_at = [DateTimeOffset]::UtcNow.ToString("o")
    qualification_level = "fixture"
    passed = $passed
    checks = $checks
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $report
Write-Output "Model runtime smoke report: $report"
if (-not $passed) { throw "model runtime fixture qualification failed" }
