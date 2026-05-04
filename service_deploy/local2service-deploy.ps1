param(
  [string]$ImageTag = "ghcr.io/scorscor/scor-vip:main",
  [string]$SshConfig = ".\ssh\tencentmain_ssh\config",
  [string]$SshHost = "tencentmain",
  [string]$RemoteDir = "/opt/scor-vip",
  [string]$GhcrTokenEnv = "GHCR_TOKEN",
  [string]$GhcrUser = "scorscor",
  [string]$AppDomain = "https://scor.vip"
)

$ErrorActionPreference = "Stop"

function Require-Command {
  param([string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Command not found: $Name"
  }
}

function Run-Step {
  param(
    [string]$Title,
    [scriptblock]$Action
  )
  Write-Host ""
  Write-Host "==> $Title"
  & $Action
}

function ConvertTo-BashDoubleQuotedLiteral {
  param([string]$Value)
  if ($null -eq $Value) {
    return ""
  }
  return $Value.Replace('\', '\\').Replace('"', '\"').Replace('$', '\$').Replace('`', '\`')
}

function Get-EnvValue {
  param([string]$Name)
  $value = [Environment]::GetEnvironmentVariable($Name, "Process")
  if ([string]::IsNullOrWhiteSpace($value)) {
    $value = [Environment]::GetEnvironmentVariable($Name, "User")
  }
  if ([string]::IsNullOrWhiteSpace($value)) {
    $value = [Environment]::GetEnvironmentVariable($Name, "Machine")
  }
  return $value
}

if ($ImageTag -notmatch '^[A-Za-z0-9._/:@-]+$') {
  throw "Invalid ImageTag: $ImageTag"
}

Require-Command ssh

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$SshConfigPath = (Resolve-Path (Join-Path $RepoRoot $SshConfig)).Path
$GhcrToken = Get-EnvValue $GhcrTokenEnv

Write-Host "Repo:       $($RepoRoot.Path)"
Write-Host "Image:      $ImageTag"
Write-Host "SSH host:   $SshHost"
Write-Host "Remote dir: $RemoteDir"
Write-Host "Domain:     $AppDomain"
if ([string]::IsNullOrWhiteSpace($GhcrToken)) {
  Write-Host "GHCR auth:  no $GhcrTokenEnv environment variable found; using existing server login or public package access"
}
else {
  Write-Host "GHCR auth:  using $GhcrTokenEnv environment variable"
}

$RemoteScriptTemplate = @'
set -euo pipefail

IMAGE_TAG="__IMAGE_TAG__"
REMOTE_DIR="__REMOTE_DIR__"
GHCR_USER="__GHCR_USER__"
GHCR_TOKEN="__GHCR_TOKEN__"
APP_DOMAIN="__APP_DOMAIN__"
COMPOSE_FILE="$REMOTE_DIR/docker-compose.yml"
ENV_FILE="$REMOTE_DIR/.env"

mkdir -p "$REMOTE_DIR"

if [ ! -f "$ENV_FILE" ]; then
  SECRET_KEY="$(openssl rand -hex 32 2>/dev/null || date +%s%N)"
  cat > "$ENV_FILE" <<EOF
SECRET_KEY=$SECRET_KEY
DATABASE_URL=sqlite:////app/instance/portfolio.db
FLASK_ENV=production
PORT=5003
APP_DOMAIN=$APP_DOMAIN
EOF
  chmod 600 "$ENV_FILE"
else
  if grep -q '^APP_DOMAIN=' "$ENV_FILE"; then
    sed -i "s|^APP_DOMAIN=.*|APP_DOMAIN=$APP_DOMAIN|" "$ENV_FILE"
  else
    printf '\nAPP_DOMAIN=%s\n' "$APP_DOMAIN" >> "$ENV_FILE"
  fi
fi

cat > "$COMPOSE_FILE" <<EOF
services:
  web:
    image: $IMAGE_TAG
    container_name: scor-vip
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "127.0.0.1:5003:5003"
    volumes:
      - scor-vip-data:/app/instance
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5003/')"]
      interval: 30s
      timeout: 10s
      start_period: 10s
      retries: 3

volumes:
  scor-vip-data:
EOF

if [ -n "$GHCR_TOKEN" ]; then
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
fi

echo "Pulling image: $IMAGE_TAG"
if command -v timeout >/dev/null 2>&1; then
  timeout 900 docker pull "$IMAGE_TAG"
else
  docker pull "$IMAGE_TAG"
fi

echo "Restarting scor-vip"
cd "$REMOTE_DIR"
docker compose pull web
docker compose up -d

echo "Waiting for health check"
for i in $(seq 1 45); do
  if docker compose exec -T web python - <<'PY' >/dev/null 2>&1
import urllib.request
urllib.request.urlopen("http://127.0.0.1:5003/", timeout=5)
PY
  then
    echo "scor-vip is healthy"
    exit 0
  fi
  sleep 2
done

echo "scor-vip did not become healthy in time" >&2
docker compose ps
docker compose logs --tail=80 web
exit 1
'@

$RemoteScript = $RemoteScriptTemplate.
  Replace("__IMAGE_TAG__", (ConvertTo-BashDoubleQuotedLiteral $ImageTag)).
  Replace("__REMOTE_DIR__", (ConvertTo-BashDoubleQuotedLiteral $RemoteDir)).
  Replace("__GHCR_USER__", (ConvertTo-BashDoubleQuotedLiteral $GhcrUser)).
  Replace("__APP_DOMAIN__", (ConvertTo-BashDoubleQuotedLiteral $AppDomain)).
  Replace("__GHCR_TOKEN__", (ConvertTo-BashDoubleQuotedLiteral $GhcrToken))

Run-Step "Pull image and deploy on server" {
  $RemoteScript | & ssh -F $SshConfigPath $SshHost "bash -s"
  if ($LASTEXITCODE -ne 0) {
    throw "ssh failed with exit code $LASTEXITCODE"
  }
}

Write-Host ""
Write-Host "Done. Deployed image: $ImageTag"
