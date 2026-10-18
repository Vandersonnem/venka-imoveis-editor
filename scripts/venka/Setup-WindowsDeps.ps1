#Requires -Version 7
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Venka Imóveis
<#
Reuses the exact upstream Windows x64 dependency lock and directory layout.
The LLVM installer is run only after SHA256 validation, into the local depot.
Run from a Visual Studio Developer PowerShell (MSVC + Windows SDK installed).
Dot-source to retain the environment: . ./scripts/venka/Setup-WindowsDeps.ps1
#>
[CmdletBinding()]
param(
    [string]$Depot = "",
    [switch]$SkipLLVMInstall
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (-not $Depot) { $Depot = Join-Path $repo '.venka-build/deps' }
$Depot = [IO.Path]::GetFullPath($Depot)
[void](New-Item -ItemType Directory -Force -Path $Depot)
$downloadDir = Join-Path $Depot 'downloads'
[void](New-Item -ItemType Directory -Force -Path $downloadDir)
$lock = Join-Path $repo 'scripts/ci/deps.lock'
$pins = @{}
foreach ($line in Get-Content -LiteralPath $lock) {
    if ($line -match '^\s*([^#\s]+)\s+(https://\S+)\s+([a-f0-9]{64})\s*$') {
        $pins[$Matches[1]] = @{ Url = $Matches[2]; SHA256 = $Matches[3] }
    }
}
$receipts = [System.Collections.Generic.List[object]]::new()
function Get-LockedDependency([string]$Name, [string]$Filename) {
    if (-not $pins.ContainsKey($Name)) { throw "No dependency '$Name' in $lock" }
    $pin = $pins[$Name]
    $destination = Join-Path $downloadDir $Filename
    if (-not (Test-Path -LiteralPath $destination) -or (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.SHA256) {
        Write-Host "Downloading pinned dependency: $Name"
        $pending = "$destination.download"
        Invoke-WebRequest -Uri $pin.Url -OutFile $pending -TimeoutSec 900 -MaximumRetryCount 3 -RetryIntervalSec 3
        $actual = (Get-FileHash -LiteralPath $pending -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $pin.SHA256) { throw "SHA256 mismatch for $Name. Untrusted download retained at $pending; expected $($pin.SHA256), got $actual" }
        Move-Item -LiteralPath $pending -Destination $destination -Force
    }
    $receipts.Add([ordered]@{ name = $Name; url = $pin.Url; sha256 = $pin.SHA256; bytes = (Get-Item -LiteralPath $destination).Length; archive = $destination })
    return $destination
}

$llvm = Get-LockedDependency 'llvm-win64' 'LLVM-21.1.0-win64.exe'
$llvmRoot = Join-Path $Depot 'llvm'
$libclang = Join-Path $llvmRoot 'bin/libclang.dll'
if (-not (Test-Path -LiteralPath $libclang)) {
    if ($SkipLLVMInstall) { throw "LLVM not installed at $llvmRoot; remove -SkipLLVMInstall to install the verified upstream file" }
    Write-Host 'Installing verified LLVM into the local build depot'
    # NSIS requires /D to be the final argument and interprets its remainder as
    # the install directory, including spaces. No shell is involved.
    $install = Start-Process -FilePath $llvm -ArgumentList @('/S', "/D=$llvmRoot") -WindowStyle Hidden -Wait -PassThru
    if ($install.ExitCode -notin @(0, 3010)) { throw "LLVM installer exited $($install.ExitCode)" }
}
if (-not (Test-Path -LiteralPath $libclang)) { throw "LLVM installation did not produce $libclang" }

$ffmpegArchive = Get-LockedDependency 'ffmpeg-win64' 'ffmpeg-win64.zip'
$ffmpegRoot = Join-Path $Depot 'ffmpeg'
if (-not (Test-Path -LiteralPath $ffmpegRoot)) { Expand-Archive -LiteralPath $ffmpegArchive -DestinationPath $ffmpegRoot }
$ffmpeg = Get-ChildItem -LiteralPath $ffmpegRoot -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'include/libavcodec/avcodec.h') } | Select-Object -First 1
if (-not $ffmpeg) { throw "FFmpeg development headers absent in $ffmpegRoot" }

$ortArchive = Get-LockedDependency 'onnxruntime-win-x64' 'onnxruntime-win-x64-1.28.0.zip'
$ort = Join-Path $Depot 'onnxruntime-win-x64-1.28.0'
if (-not (Test-Path -LiteralPath $ort)) { Expand-Archive -LiteralPath $ortArchive -DestinationPath $Depot }
foreach ($file in @('onnxruntime.lib', 'onnxruntime.dll')) {
    if (-not (Test-Path -LiteralPath (Join-Path $ort "lib/$file"))) { throw "Missing ONNX Runtime file: $file" }
}

$sherpaArchive = Get-LockedDependency 'sherpa-onnx-win-x64-shared-MT-Release-lib' 'sherpa-onnx-win-x64.tar.bz2'
$sherpa = Join-Path $Depot 'sherpa-onnx-v1.13.7-win-x64-shared-MT-Release-lib'
if (-not (Test-Path -LiteralPath $sherpa)) {
    $python = Get-Command python.exe -ErrorAction Stop
    & $python.Source -c 'import sys,tarfile; t=tarfile.open(sys.argv[1]); t.extractall(sys.argv[2],filter="data")' $sherpaArchive $Depot
    if ($LASTEXITCODE -ne 0) { throw 'Python failed to extract sherpa-onnx' }
}
$sherpaLib = Join-Path $Depot 'sherpa-libs'
$sherpaDll = Join-Path $Depot 'sherpa-dlls'
[void](New-Item -ItemType Directory -Force -Path $sherpaLib, $sherpaDll)
Copy-Item -Path (Join-Path $sherpa 'lib/sherpa-onnx-*.lib') -Destination $sherpaLib -Force
Copy-Item -Path (Join-Path $sherpa 'lib/sherpa-onnx-*.dll') -Destination $sherpaDll -Force
if (-not (Get-ChildItem -LiteralPath $sherpaLib -Filter '*.lib')) { throw 'No sherpa-onnx import library' }
if (Get-ChildItem -LiteralPath $sherpaLib -Filter '*.dll') { throw 'SHERPA_ONNX_LIB_DIR must not contain runtime DLLs under the app Cargo profile' }

$env:FFMPEG_DIR = $ffmpeg.FullName
$env:LIBCLANG_PATH = Join-Path $llvmRoot 'bin'
$env:ORT_DIR = $ort
$env:ORT_LIB_LOCATION = Join-Path $ort 'lib'
$env:ORT_PREFER_DYNAMIC_LINK = '1'
$env:SHERPA_ONNX_LIB_DIR = $sherpaLib
$env:SHERPA_DLL_DIR = $sherpaDll
$env:GGML_NATIVE = 'OFF'
$env:GGML_BACKEND_DL = 'ON'
$env:GGML_CPU_ALL_VARIANTS = 'ON'
$env:GGML_AVX2 = 'OFF'
$env:GGML_FMA = 'OFF'
$env:GGML_F16C = 'OFF'
$env:GGML_BMI2 = 'OFF'
$env:PATH = "$env:LIBCLANG_PATH;$env:FFMPEG_DIR\bin;$env:ORT_LIB_LOCATION;$sherpaDll;$env:PATH"
$receipt = [ordered]@{ time = (Get-Date).ToUniversalTime().ToString('o'); architecture = 'x86_64-pc-windows-msvc'; lock = $lock; dependencies = $receipts; environment = @{
    FFMPEG_DIR = $env:FFMPEG_DIR; LIBCLANG_PATH = $env:LIBCLANG_PATH; ORT_LIB_LOCATION = $env:ORT_LIB_LOCATION;
    SHERPA_ONNX_LIB_DIR = $env:SHERPA_ONNX_LIB_DIR; SHERPA_DLL_DIR = $env:SHERPA_DLL_DIR;
} }
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Depot 'DEPENDENCIES_VERIFIED.json') -Encoding utf8
Write-Host "Dependency environment ready. Receipt: $Depot\DEPENDENCIES_VERIFIED.json"
Write-Host 'Next: cd src; cargo build --locked --profile app -p concat --target x86_64-pc-windows-msvc'
