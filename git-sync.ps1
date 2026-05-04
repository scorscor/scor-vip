param(
    [Parameter(Position = 0)]
    [string]$Message = "update scor vip",

    [string]$RemoteUrl = "https://github.com/scorscor/scor-vip.git",

    [string]$Branch = "main",

    [string]$Workflow = "Docker Image",

    [int]$Limit = 5,

    [switch]$OpenLatest,

    [switch]$Once,

    [int]$IntervalSeconds = 10,

    [switch]$SkipActionStatus,

    [switch]$ActionStatusOnly
)

$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot

Set-Location -LiteralPath $RepoRoot

function Resolve-Gh {
    $cmd = Get-Command gh -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $defaultPath = "C:\Program Files\GitHub CLI\gh.exe"
    if (Test-Path -LiteralPath $defaultPath) {
        return $defaultPath
    }

    throw "GitHub CLI not found. Install gh or add it to PATH."
}

function Assert-GhAuth {
    param([string]$GhPath)

    $authOutput = & $GhPath auth status 2>&1
    if ($LASTEXITCODE -ne 0) {
        $authOutput | ForEach-Object { Write-Host $_ }
        throw "gh is not logged in. Run: gh auth login"
    }
}

function Show-ActionStatus {
    param(
        [string]$GhPath,
        [string]$WorkflowName,
        [int]$RunLimit,
        [bool]$WatchMode
    )

    $script:LatestRun = $null

    Write-Host "Workflow: $WorkflowName  |  Updated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    if ($WatchMode) {
        Write-Host "Refreshing every $IntervalSeconds seconds. Press Ctrl+C to stop."
    }
    Write-Host ""

    & $GhPath run list --workflow $WorkflowName --limit $RunLimit
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to list workflow runs."
    }

    $latestJson = & $GhPath run list --workflow $WorkflowName --limit 1 --json databaseId,status,conclusion,headBranch,headSha,displayTitle,url,createdAt
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to read latest workflow run."
    }

    $latest = $latestJson | ConvertFrom-Json
    if (-not $latest -or $latest.Count -eq 0) {
        Write-Host ""
        Write-Host "No workflow runs found."
        return
    }

    $script:LatestRun = $latest[0]
}

function Watch-GitHubActions {
    if ($IntervalSeconds -lt 2) {
        $script:IntervalSeconds = 2
    }

    $gh = Resolve-Gh
    Assert-GhAuth -GhPath $gh

    $openedLatest = $false
    do {
        Clear-Host
        Show-ActionStatus -GhPath $gh -WorkflowName $Workflow -RunLimit $Limit -WatchMode:(-not $Once)

        if ($OpenLatest -and -not $openedLatest -and $script:LatestRun) {
            Start-Process $script:LatestRun.url
            $openedLatest = $true
        }

        if ($Once) {
            break
        }

        Start-Sleep -Seconds $IntervalSeconds
    } while ($true)
}

if ($ActionStatusOnly) {
    Watch-GitHubActions
    exit 0
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is not installed or not available in PATH."
}

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
    throw "This script must be run from the scor-vip Git repository."
}

$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
if (-not $currentBranch -or $currentBranch -eq "HEAD") {
    throw "Unable to detect the current Git branch."
}

$originUrl = (git remote get-url origin 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($originUrl)) {
    Write-Host "[git-sync] Adding origin: $RemoteUrl"
    git remote add origin $RemoteUrl
}
elseif ($originUrl.Trim() -ne $RemoteUrl) {
    Write-Host "[git-sync] Updating origin: $RemoteUrl"
    git remote set-url origin $RemoteUrl
}

if ($currentBranch -ne $Branch) {
    Write-Host "[git-sync] Renaming branch '$currentBranch' to '$Branch'"
    git branch -M $Branch
    $currentBranch = $Branch
}

$statusLines = @(git status --porcelain)
if ($statusLines.Count -eq 0) {
    Write-Host "[git-sync] No local changes to commit."
}
else {
    Write-Host "[git-sync] Branch: $currentBranch"
    Write-Host "[git-sync] Commit message: $Message"
    git add .
    git commit -m $Message
}

$upstream = git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($upstream)) {
    git push -u origin $currentBranch
}
else {
    git push
}

Write-Host "[git-sync] Done. Pushed to origin/$currentBranch."

if (-not $SkipActionStatus) {
    Write-Host "[git-sync] Opening GitHub Actions status..."
    Start-Sleep -Seconds 2
    Watch-GitHubActions
}
