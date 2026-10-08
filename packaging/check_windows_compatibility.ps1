param([string]$PortableDirectory = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $PortableDirectory).Path
$exe = Join-Path $root 'current\AnClicker.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw 'Place this script beside An Clicker.exe, or pass -PortableDirectory with the extracted portable folder.'
}
$reportRoot = Join-Path $root ('compatibility-report-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $reportRoot | Out-Null
$names = @('ANCLICKER_DATA_DIR','ANCLICKER_SINGLETON_KEY','QT_QPA_PLATFORM','QT_SCALE_FACTOR')
$previous = @{}
foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
$runs = @()
try {
    foreach ($scale in @('1','1.25','1.5','2')) {
        $data = Join-Path $reportRoot ('scale-' + $scale)
        New-Item -ItemType Directory -Path $data | Out-Null
        $env:ANCLICKER_DATA_DIR = $data
        $env:ANCLICKER_SINGLETON_KEY = 'compat-' + [guid]::NewGuid().ToString('N')
        $env:QT_QPA_PLATFORM = 'windows'
        $env:QT_SCALE_FACTOR = $scale
        $process = Start-Process -FilePath $exe -ArgumentList '--startup-smoke-test' -WorkingDirectory $root -PassThru -WindowStyle Hidden
        if (-not $process.WaitForExit(120000)) {
            Stop-Process -Id $process.Id
            throw "Startup timed out at scale $scale"
        }
        $process.Refresh()
        $readyFile = Join-Path $data 'startup-ready.json'
        if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $readyFile)) {
            throw "Startup failed at scale $scale; exit=$($process.ExitCode). See $data\logs"
        }
        $ready = Get-Content -LiteralPath $readyFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $ready.ready -or -not $ready.full_checks -or $ready.runtime.binding -ne 'PySide2' -or -not $ready.ocr_validation.rapidocr) {
            throw "Incomplete runtime validation at scale $scale"
        }
        $runs += @{ scale = $scale; result = $ready }
    }
    @{ passed = $true; os = (Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture);
       executableSha256 = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash; runs = $runs } |
        ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $reportRoot 'result.json') -Encoding UTF8
    Write-Host "PASS: $reportRoot\result.json"
} catch {
    @{ passed = $false; error = $_.Exception.Message; runs = $runs } | ConvertTo-Json -Depth 12 |
        Set-Content -LiteralPath (Join-Path $reportRoot 'result.json') -Encoding UTF8
    throw
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process') }
}
