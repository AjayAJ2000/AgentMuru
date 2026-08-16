[CmdletBinding()]
param(
    [ValidateRange(1, 600)]
    [int]$DurationSeconds = 60,
    [ValidateRange(16, 4096)]
    [int]$WorkingSetLimitMiB = 150,
    [string]$GoExecutable = "go",
    [string]$ReportPath = ".tmp/qualification/edge-idle.json"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$edgeRoot = Join-Path $repositoryRoot "edge"
$temporaryRoot = Join-Path $repositoryRoot ".tmp/qualification"
$binaryPath = Join-Path $temporaryRoot "muru-idle.exe"
$resolvedReport = if ([System.IO.Path]::IsPathRooted($ReportPath)) {
    $ReportPath
} else {
    Join-Path $repositoryRoot $ReportPath
}

New-Item -ItemType Directory -Force $temporaryRoot | Out-Null
New-Item -ItemType Directory -Force (Split-Path -Parent $resolvedReport) | Out-Null

Push-Location $edgeRoot
try {
    & $GoExecutable build -trimpath -o $binaryPath ./cmd/muru
    if ($LASTEXITCODE -ne 0) {
        throw "native AgentMuru build failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

$probeDuration = $DurationSeconds + 5
$process = Start-Process `
    -FilePath $binaryPath `
    -ArgumentList @("qualification-idle", "--duration", "${probeDuration}s") `
    -WindowStyle Hidden `
    -PassThru

$samples = [System.Collections.Generic.List[object]]::new()
$logicalProcessors = [Math]::Max(1, [Environment]::ProcessorCount)
$previousCpu = [TimeSpan]::Zero
$previousAt = [DateTimeOffset]::UtcNow

try {
    for ($index = 0; $index -lt $DurationSeconds; $index++) {
        Start-Sleep -Seconds 1
        $process.Refresh()
        if ($process.HasExited) {
            throw "idle probe exited before the ${DurationSeconds}s measurement completed"
        }

        $sampledAt = [DateTimeOffset]::UtcNow
        $cpu = $process.TotalProcessorTime
        $elapsedMs = [Math]::Max(1, ($sampledAt - $previousAt).TotalMilliseconds)
        $cpuPercent = (($cpu - $previousCpu).TotalMilliseconds / $elapsedMs / $logicalProcessors) * 100
        $samples.Add([pscustomobject][ordered]@{
            second = $index + 1
            working_set_bytes = $process.WorkingSet64
            cpu_percent = [Math]::Round($cpuPercent, 4)
        })
        $previousCpu = $cpu
        $previousAt = $sampledAt
    }
} finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id
        $process.WaitForExit()
    }
}

$peakWorkingSet = ($samples | Measure-Object -Property working_set_bytes -Maximum).Maximum
$averageCpu = ($samples | Measure-Object -Property cpu_percent -Average).Average
$limitBytes = $WorkingSetLimitMiB * 1MB
$passed = $peakWorkingSet -lt $limitBytes

$report = [ordered]@{
    schema_version = "qualification.agentmuru.dev/edge-idle/v1"
    generated_at = [DateTimeOffset]::UtcNow.ToString("o")
    duration_seconds = $DurationSeconds
    sample_count = $samples.Count
    peak_working_set_bytes = $peakWorkingSet
    average_cpu_percent = [Math]::Round($averageCpu, 4)
    working_set_limit_bytes = $limitBytes
    passed = $passed
    samples = $samples
}

$report | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $resolvedReport
Write-Output "Idle qualification report: $resolvedReport"
Write-Output "Peak working set: $([Math]::Round($peakWorkingSet / 1MB, 2)) MiB"
Write-Output "Average CPU: $([Math]::Round($averageCpu, 4))%"

if (-not $passed) {
    throw "bootstrap working set reached or exceeded ${WorkingSetLimitMiB} MiB"
}
