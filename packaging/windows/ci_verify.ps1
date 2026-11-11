$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Zip = Join-Path $Root 'dist\HRAssistant-windows.zip'
if (-not (Test-Path $Zip)) { throw "missing $Zip" }

$Unpack = Join-Path $env:RUNNER_TEMP 'hr-unpack'
if (Test-Path $Unpack) { Remove-Item -Recurse -Force $Unpack }
Expand-Archive -Path $Zip -DestinationPath $Unpack
$Bat = Join-Path $Unpack 'HRAssistant\安装.bat'
if (-not (Test-Path -LiteralPath $Bat)) { throw "installer not found in zip: $Bat" }

$MarkerDir = Join-Path $env:USERPROFILE '.boss-agent'
New-Item -ItemType Directory -Force -Path $MarkerDir | Out-Null
$Marker = Join-Path $MarkerDir 'ci-keep.txt'
Set-Content -Path $Marker -Value 'keep' -Encoding utf8NoBOM

function Install-Assistant([string]$Dest) {
    $env:BOSS_INSTALL_DIR = $Dest
    $env:BOSS_INSTALL_NONINTERACTIVE = '1'
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    & cmd.exe /c "`"$Bat`""
    if ($LASTEXITCODE -ne 0) { throw "install failed for ${Dest}: $LASTEXITCODE" }
}

function Assert-StillThere {
    if (-not (Test-Path -LiteralPath $Marker)) { throw 'installer removed ~/.boss-agent data' }
    $text = (Get-Content -LiteralPath $Marker -Raw).Trim()
    if ($text -ne 'keep') { throw 'installer changed ~/.boss-agent marker' }
}

$Dest = Join-Path $env:RUNNER_TEMP 'HRAssistant-install'
Install-Assistant $Dest
Assert-StillThere
Install-Assistant $Dest
Assert-StillThere

$Python = Join-Path $Dest 'runtime\python.exe'
$Verify = Join-Path $Root 'packaging\windows\verify_install.py'
$Boss = Join-Path $Dest 'boss.cmd'
& $Python $Verify $Boss
if ($LASTEXITCODE -ne 0) { throw 'ascii path verification failed' }

$Chinese = Join-Path $env:RUNNER_TEMP '张三的招聘目录'
Install-Assistant $Chinese
Assert-StillThere
$ChineseBoss = Join-Path $Chinese 'boss.cmd'
& (Join-Path $Chinese 'runtime\python.exe') $Verify $ChineseBoss
if ($LASTEXITCODE -ne 0) { throw 'chinese path verification failed' }

$Probe = Join-Path $Root 'packaging\windows\probe_win_cookies.py'
$ProbeOut = Join-Path $Root 'cookie-probe.txt'
& $Python $Probe | Tee-Object -FilePath $ProbeOut
if ($LASTEXITCODE -ne 0) { throw 'cookie probe failed' }
