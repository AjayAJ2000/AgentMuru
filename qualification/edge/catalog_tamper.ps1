[CmdletBinding()]
param(
    [string]$GoExecutable = "go",
    [string]$ReportPath = ".tmp/qualification/catalog-tamper.json"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$report = if ([System.IO.Path]::IsPathRooted($ReportPath)) { $ReportPath } else { Join-Path $repositoryRoot $ReportPath }
New-Item -ItemType Directory -Force (Split-Path -Parent $report) | Out-Null

$checks = @()
Push-Location (Join-Path $repositoryRoot "edge")
try {
    & $GoExecutable test ./internal/catalog -run "TestVerifyRejectsMutatedCatalog|TestCommittedCatalogFixtureHasAValidSignature" -count=1
    $catalogPassed = $LASTEXITCODE -eq 0
    $checks += [pscustomobject][ordered]@{ name = "catalog signature mutation rejected"; passed = $catalogPassed }

    & $GoExecutable test ./internal/download -run "TestFetchNeverPromotesWrongDigest|TestFetchRejectsMoreThanDeclaredSize" -count=1
    $artifactPassed = $LASTEXITCODE -eq 0
    $checks += [pscustomobject][ordered]@{ name = "artifact mutation rejected before promotion"; passed = $artifactPassed }
} finally {
    Pop-Location
}

$passed = ($checks | Where-Object { -not $_.passed }).Count -eq 0
[ordered]@{
    schema_version = "qualification.agentmuru.dev/edge-runtime/v1"
    generated_at = [DateTimeOffset]::UtcNow.ToString("o")
    qualification_level = "fixture"
    passed = $passed
    checks = $checks
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $report
Write-Output "Catalog tamper report: $report"
if (-not $passed) { throw "catalog or artifact tamper qualification failed" }
