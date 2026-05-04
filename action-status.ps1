param(
  [string]$Workflow = "Docker Image",
  [int]$Limit = 5,
  [switch]$OpenLatest,
  [switch]$Once,
  [int]$IntervalSeconds = 10
)

$ErrorActionPreference = "Stop"

$gitSyncScript = Join-Path $PSScriptRoot "git-sync.ps1"

& $gitSyncScript `
  -ActionStatusOnly `
  -Workflow $Workflow `
  -Limit $Limit `
  -IntervalSeconds $IntervalSeconds `
  -OpenLatest:$OpenLatest `
  -Once:$Once

exit $LASTEXITCODE
