[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$IncludeBuildArtifacts,
    [string]$ValidateTarget
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
$repoPrefix = $repoRoot + [System.IO.Path]::DirectorySeparatorChar
$forbiddenTargets = @(
    (Join-Path $repoRoot ".worktrees"),
    (Join-Path $repoRoot "Branding_Files"),
    (Join-Path $repoRoot "brickflowui/frontend/dist")
) | ForEach-Object { [System.IO.Path]::GetFullPath($_) }

function Assert-SafeRepoTarget([string]$Path) {
    $resolved = [System.IO.Path]::GetFullPath($Path)
    if ($resolved -eq $repoRoot -or -not $resolved.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing cleanup outside repository: $resolved"
    }
    foreach ($forbidden in $forbiddenTargets) {
        if ($resolved -eq $forbidden -or $resolved.StartsWith($forbidden + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing protected cleanup target: $resolved"
        }
    }
    $relativePath = $resolved.Substring($repoPrefix.Length)
    $currentPath = $repoRoot
    foreach ($component in $relativePath.Split([System.IO.Path]::DirectorySeparatorChar, [System.StringSplitOptions]::RemoveEmptyEntries)) {
        $currentPath = Join-Path $currentPath $component
        if (Test-Path -LiteralPath $currentPath) {
            $item = Get-Item -LiteralPath $currentPath -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Refusing cleanup through reparse point: $currentPath"
            }
        }
    }
    return $resolved
}

function Remove-RepoTarget([string]$Path) {
    $resolved = Assert-SafeRepoTarget $Path
    if (Test-Path -LiteralPath $resolved) {
        if ($PSCmdlet.ShouldProcess($resolved, "Remove generated artifact")) {
            Remove-Item -LiteralPath $resolved -Recurse -Force
        }
    }
}

if ($PSBoundParameters.ContainsKey("ValidateTarget")) {
    [void](Assert-SafeRepoTarget $ValidateTarget)
    return
}

$targets = @(
    (Join-Path $repoRoot ".tmp"),
    (Join-Path $repoRoot ".pytest_cache"),
    (Join-Path $repoRoot "site")
)
$targets += Get-ChildItem -LiteralPath $repoRoot -Directory -Filter "pytest-cache-files-*" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
$targets += Get-ChildItem -LiteralPath $repoRoot -Directory -Filter "_tmp_cli_*" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }

foreach ($sourceRoot in "brickflowui", "tests", "examples") {
    $sourcePath = Join-Path $repoRoot $sourceRoot
    if (Test-Path -LiteralPath $sourcePath) {
        $targets += Get-ChildItem -LiteralPath $sourcePath -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
    }
}

if ($IncludeBuildArtifacts) {
    $targets += @(
        (Join-Path $repoRoot "dist"),
        (Join-Path $repoRoot "build"),
        (Join-Path $repoRoot "frontend/node_modules")
    )
}

$targets | Select-Object -Unique | ForEach-Object { Remove-RepoTarget $_ }
