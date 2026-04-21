param(
  [string]$RepoRoot = "C:\PA-Framework\zip-review",
  [string]$LogDir = "$PSScriptRoot\logs"
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
$log = Join-Path $LogDir "smoke-$ts.log"

function Log($m) {
  $line = "[$(Get-Date -Format 'HH:mm:ss')] $m"
  $line | Tee-Object -FilePath $log -Append
}

function Run-Cmd($title, $command) {
  Log "--- $title ---"
  Log "CMD> $command"
  $p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $command" -Wait -PassThru -NoNewWindow
  Log "EXIT=$($p.ExitCode)"
  return $p.ExitCode
}

Log "Windows real smoke test starting"
Log "RepoRoot=$RepoRoot"
Log "OS=$([System.Environment]::OSVersion.VersionString)"

if (!(Test-Path (Join-Path $RepoRoot 'pa.bat'))) {
  throw "pa.bat not found at $RepoRoot"
}

# Scenario 1: actual machine (no mocks)
$exit1 = Run-Cmd "Scenario 1 - actual machine bootstrap" "cd /d \"$RepoRoot\" && pa.bat --help"

# Scenario 2: OpenCode missing simulation (without uninstalling global tools)
$shim = Join-Path $env:TEMP "pa-smoke-shim-$ts"
New-Item -ItemType Directory -Force -Path $shim | Out-Null

# keep python available by forwarding to detected python launcher if present
$realPython = (Get-Command py -ErrorAction SilentlyContinue)?.Source
if (-not $realPython) { $realPython = (Get-Command python -ErrorAction SilentlyContinue)?.Source }
if ($realPython) {
  @"
@echo off
\"$realPython\" %*
"@ | Set-Content -Encoding ASCII (Join-Path $shim 'python.cmd')
}

# hide opencode from PATH by controlling PATH precedence, but allow npm
$cmd2 = "set PATH=$shim;C:\Windows\System32;%PATH% && cd /d \"$RepoRoot\" && pa.bat --help"
$exit2 = Run-Cmd "Scenario 2 - opencode absent path-precedence" $cmd2

Log "Summary: scenario1=$exit1 scenario2=$exit2"
Log "Smoke test finished. Log: $log"

if ($exit1 -ne 0) { exit 1 }
if ($exit2 -ne 0) { exit 2 }
exit 0
