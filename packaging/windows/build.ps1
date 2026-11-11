$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Version = '3.12.10'
$EmbedUrl = "https://www.python.org/ftp/python/$Version/python-$Version-embed-amd64.zip"
$EmbedSha256 = '4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3'
$Stage = Join-Path $Root 'dist\hr-assistant-stage'
$Bundle = Join-Path $Stage 'HRAssistant'
$ZipPath = Join-Path $Root 'dist\HRAssistant-windows.zip'

if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
New-Item -ItemType Directory -Path (Join-Path $Bundle 'runtime') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Root 'dist') -Force | Out-Null

$EmbedZip = Join-Path $Stage 'python-embed.zip'
Write-Host "Downloading $EmbedUrl"
Invoke-WebRequest -Uri $EmbedUrl -OutFile $EmbedZip
$actual = (Get-FileHash -Algorithm SHA256 -Path $EmbedZip).Hash.ToLowerInvariant()
if ($actual -ne $EmbedSha256) { throw "embeddable python hash mismatch: $actual" }
Expand-Archive -Path $EmbedZip -DestinationPath (Join-Path $Bundle 'runtime') -Force

$Pth = Get-ChildItem (Join-Path $Bundle 'runtime') -Filter 'python*._pth' | Select-Object -First 1
if (-not $Pth) { throw 'python ._pth not found' }
$lines = @(Get-Content -Path $Pth.FullName)
$zipLine = $lines | Where-Object { $_ -like 'python*.zip' } | Select-Object -First 1
if (-not $zipLine) { $zipLine = 'python312.zip' }
@(
    $zipLine
    '.'
    'Lib\site-packages'
    'import site'
) | Set-Content -Path $Pth.FullName -Encoding ascii
New-Item -ItemType Directory -Path (Join-Path $Bundle 'runtime\Lib\site-packages') -Force | Out-Null

$Python = Join-Path $Bundle 'runtime\python.exe'
$GetPip = Join-Path $Stage 'get-pip.py'
Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile $GetPip
& $Python $GetPip --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw "get-pip failed: $LASTEXITCODE" }

$WheelDir = Join-Path $Stage 'wheel'
New-Item -ItemType Directory -Path $WheelDir -Force | Out-Null
Push-Location $Root
try {
    uv build --wheel --out-dir $WheelDir
    if ($LASTEXITCODE -ne 0) { throw "uv build failed: $LASTEXITCODE" }
} finally {
    Pop-Location
}
$Wheel = Get-ChildItem $WheelDir -Filter 'boss_agent_cli-*.whl' | Select-Object -First 1
if (-not $Wheel) { throw 'wheel not found' }
& $Python -m pip install --disable-pip-version-check --no-warn-script-location $Wheel.FullName
if ($LASTEXITCODE -ne 0) { throw "pip install failed: $LASTEXITCODE" }
& $Python -c "from boss_agent_cli import __version__; print(__version__)"
if ($LASTEXITCODE -ne 0) { throw 'embedded import failed' }

$names = @(
    '安装.bat',
    'boss.cmd',
    'boss_launch.py',
    'explain_doctor.py',
    'add_user_path.ps1',
    '使用说明.txt',
    '给Agent的说明.md'
)
foreach ($name in $names) {
    Copy-Item -Path (Join-Path $PSScriptRoot $name) -Destination (Join-Path $Bundle $name) -Force
}

$forbidden = Get-ChildItem $Bundle -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -in @('Cookies', 'session.enc', 'wt2') -or $_.FullName -match '\\\.boss-agent\\'
}
if ($forbidden) { throw 'bundle contains private browser or login files' }

if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $Bundle,
    $ZipPath,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $true
)
Write-Host "Wrote $ZipPath"
