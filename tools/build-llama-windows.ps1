[CmdletBinding()]
param(
    [string]$OutputDirectory = "artifacts/llama-windows",
    [string]$SourceDirectory = ""
)

$ErrorActionPreference = "Stop"
$llamaCommit = "3cb7ffb1a1f612d5e4a46244ae5a3c77ad934a70"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outputRoot = if ([System.IO.Path]::IsPathRooted($OutputDirectory)) { $OutputDirectory } else { Join-Path $repositoryRoot $OutputDirectory }
$sourceRoot = if ($SourceDirectory) {
    (Resolve-Path $SourceDirectory).Path
} else {
    Join-Path $repositoryRoot ".tmp/llama-$llamaCommit"
}

New-Item -ItemType Directory -Force $outputRoot | Out-Null
if (-not (Test-Path (Join-Path $sourceRoot ".git"))) {
    git clone https://github.com/ggml-org/llama.cpp.git $sourceRoot
    if ($LASTEXITCODE -ne 0) { throw "llama.cpp clone failed" }
}

Push-Location $sourceRoot
try {
    git fetch --depth 1 origin $llamaCommit
    if ($LASTEXITCODE -ne 0) { throw "llama.cpp commit fetch failed" }
    git checkout --detach $llamaCommit
    if ($LASTEXITCODE -ne 0) { throw "llama.cpp checkout failed" }

    $common = @(
        "-G", "Ninja Multi-Config",
        "-DGGML_NATIVE=OFF",
        "-DLLAMA_BUILD_SERVER=ON",
        "-DLLAMA_BUILD_TESTS=OFF",
        "-DLLAMA_BUILD_EXAMPLES=OFF",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DGGML_BACKEND_DL=OFF",
        "-DGGML_CUDA=OFF",
        "-DGGML_VULKAN=OFF",
        "-DGGML_AVX512=OFF",
        "-DGGML_AVX512_VBMI=OFF",
        "-DGGML_AVX512_VNNI=OFF"
    )
    $variants = @(
        [ordered]@{ id = "windows-x64-baseline"; rank = 10; required_cpu_flags = @("sse4.2"); flags = @("-DGGML_SSE42=ON", "-DGGML_AVX=OFF", "-DGGML_AVX2=OFF", "-DGGML_BMI2=OFF") },
        [ordered]@{ id = "windows-x64-avx"; rank = 20; required_cpu_flags = @("sse4.2", "avx"); flags = @("-DGGML_SSE42=ON", "-DGGML_AVX=ON", "-DGGML_AVX2=OFF", "-DGGML_BMI2=OFF") },
        [ordered]@{ id = "windows-x64-avx2"; rank = 30; required_cpu_flags = @("sse4.2", "avx", "avx2"); flags = @("-DGGML_SSE42=ON", "-DGGML_AVX=ON", "-DGGML_AVX2=ON", "-DGGML_BMI2=ON") }
    )

    $manifestVariants = @()
    foreach ($variant in $variants) {
        $buildDirectory = Join-Path $sourceRoot ("build-agentmuru-" + $variant.id)
        & cmake -S $sourceRoot -B $buildDirectory @common @($variant.flags)
        if ($LASTEXITCODE -ne 0) { throw "CMake configure failed for $($variant.id)" }
        & cmake --build $buildDirectory --config Release --target llama-server
        if ($LASTEXITCODE -ne 0) { throw "CMake build failed for $($variant.id)" }
        $built = Get-ChildItem $buildDirectory -Recurse -Filter "llama-server.exe" | Select-Object -First 1
        if (-not $built) { throw "llama-server.exe was not produced for $($variant.id)" }
        $filename = "llama-server-$($variant.id).exe"
        $destination = Join-Path $outputRoot $filename
        Copy-Item -LiteralPath $built.FullName -Destination $destination -Force
        $file = Get-Item -LiteralPath $destination
        $manifestVariants += [ordered]@{
            id = $variant.id
            os = "windows"
            architecture = "amd64"
            required_cpu_flags = $variant.required_cpu_flags
            rank = $variant.rank
            filename = $filename
            size_bytes = $file.Length
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash.ToLowerInvariant()
            cmake_flags = $common + $variant.flags
        }
    }
} finally {
    Pop-Location
}

$manifest = [ordered]@{
    schema_version = "runtime-manifest.agentmuru.dev/v1"
    llama_cpp_commit = $llamaCommit
    generated_at = [DateTimeOffset]::UtcNow.ToString("o")
    variants = $manifestVariants
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $outputRoot "manifest.json")
Write-Output "Runtime manifest: $(Join-Path $outputRoot 'manifest.json')"
