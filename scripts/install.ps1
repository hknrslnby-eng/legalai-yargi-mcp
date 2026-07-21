param(
    [string[]]$Ide = @("all"),
    [switch]$Repair,
    [switch]$DryRun,
    [switch]$OnlyInstalled,
    [string]$DataDir
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Uv = Join-Path $Root "runtime\uv.exe"
$App = Join-Path $Root "app"
$arguments = @("run", "--directory", $App, "socratlegal", "install", "--install-dir", $App, "--portable-root", $Root)
foreach ($item in $Ide) { $arguments += @("--ide", $item) }
if ($Repair) { $arguments += "--repair" }
if ($DryRun) { $arguments += "--dry-run" }
if ($OnlyInstalled) { $arguments += "--only-installed" }
if ($DataDir) { $arguments += @("--data-dir", $DataDir) }
& $Uv @arguments
exit $LASTEXITCODE
