[CmdletBinding()]
param(
    [string]$Version = "v0.3.0-alpha.1",
    [string]$InstallDirectory = (Join-Path $env:LOCALAPPDATA "Programs/AgentMuru"),
    [switch]$AddToPath,
    [string]$ArchivePath = "",
    [string]$ChecksumPath = ""
)

$ErrorActionPreference = "Stop"
if (-not [Environment]::Is64BitOperatingSystem) { throw "This preview currently requires 64-bit Windows." }
if (-not $env:LOCALAPPDATA) { throw "LOCALAPPDATA is required." }

$temporaryRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$work = Join-Path $temporaryRoot ("agentmuru-install-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force $work | Out-Null
try {
    $archive = if ($ArchivePath) { (Resolve-Path $ArchivePath).Path } else { Join-Path $work "agentmuru.zip" }
    $checksum = if ($ChecksumPath) { (Resolve-Path $ChecksumPath).Path } else { Join-Path $work "agentmuru.zip.sha256" }
    if (-not $ArchivePath) {
        $name = "agentmuru-$Version-windows-x64.zip"
        $base = "https://github.com/AjayAJ2000/AgentMuru/releases/download/$Version"
        Invoke-WebRequest -UseBasicParsing -Uri "$base/$name" -OutFile $archive
        Invoke-WebRequest -UseBasicParsing -Uri "$base/$name.sha256" -OutFile $checksum
    }

    $expected = ((Get-Content $checksum -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
    if ($expected -notmatch "^[0-9a-f]{64}$") { throw "The release checksum file is invalid." }
    $actual = (Get-FileHash -Algorithm SHA256 $archive).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "The AgentMuru archive checksum did not match." }

    $expanded = Join-Path $work "expanded"
    Expand-Archive -LiteralPath $archive -DestinationPath $expanded
    $source = Join-Path $expanded "muru.exe"
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "The archive does not contain muru.exe." }
    New-Item -ItemType Directory -Force $InstallDirectory | Out-Null
    Copy-Item -LiteralPath $source -Destination (Join-Path $InstallDirectory "muru.exe") -Force

    if ($AddToPath) {
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        $entries = @($userPath -split ";" | Where-Object { $_ })
        if ($entries -notcontains $InstallDirectory) {
            [Environment]::SetEnvironmentVariable("Path", (($entries + $InstallDirectory) -join ";"), "User")
        }
        if (($env:Path -split ";") -notcontains $InstallDirectory) { $env:Path = "$InstallDirectory;$env:Path" }
    }

    & (Join-Path $InstallDirectory "muru.exe") version
    Write-Output "Installed AgentMuru to $InstallDirectory"
    if (-not $AddToPath) { Write-Output "Add that directory to PATH, or rerun with -AddToPath." }
} finally {
    $resolvedWork = [System.IO.Path]::GetFullPath($work)
    if ($resolvedWork.StartsWith($temporaryRoot, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $resolvedWork)) {
        Remove-Item -LiteralPath $resolvedWork -Recurse -Force
    }
}
