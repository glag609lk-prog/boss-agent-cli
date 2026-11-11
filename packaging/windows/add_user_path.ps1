param(
    [Parameter(Mandatory = $true)]
    [string]$Dir
)
$ErrorActionPreference = 'Stop'
$norm = $Dir.TrimEnd('\')
$current = [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not $current) { $current = '' }
$items = New-Object System.Collections.Generic.List[string]
foreach ($part in ($current -split ';')) {
    $trimmed = $part.Trim()
    if (-not $trimmed) { continue }
    if ($trimmed.TrimEnd('\') -ieq $norm) { continue }
    $items.Add($trimmed)
}
$items.Add($norm)
[Environment]::SetEnvironmentVariable('Path', ($items -join ';'), 'User')
