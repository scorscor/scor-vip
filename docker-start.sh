#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

PROJECT_NAME="${PROJECT_NAME:-scor-vip}"
COMPOSE_FILE_INPUT="${COMPOSE_FILE:-docker-compose.yml}"
ACTION="${1:-start}"
DB_FILE_INPUT="${DB_FILE:-./instance/portfolio.db}"

case "$COMPOSE_FILE_INPUT" in
  /*) COMPOSE_FILE_PATH="$COMPOSE_FILE_INPUT" ;;
  *) COMPOSE_FILE_PATH="$SCRIPT_DIR/$COMPOSE_FILE_INPUT" ;;
esac

case "$DB_FILE_INPUT" in
  /*) DB_FILE_PATH="$DB_FILE_INPUT" ;;
  *) DB_FILE_PATH="$SCRIPT_DIR/$DB_FILE_INPUT" ;;
esac

if ! command -v docker >/dev/null 2>&1; then
  echo "[error] Docker is not installed." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "[error] Docker is not running or current user cannot access Docker." >&2
  exit 1
fi

if [ ! -f "$COMPOSE_FILE_PATH" ]; then
  echo "[error] Compose file not found: $COMPOSE_FILE_PATH" >&2
  exit 1
fi

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE_PATH" "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE_PATH" "$@"
  else
    echo "[error] Docker Compose is not installed." >&2
    exit 1
  fi
}

remove_manual_container() {
  container_name="$1"
  if docker ps -a --format '{{.Names}}' | grep -qx "$container_name"; then
    echo "[info] Removing old manual container: $container_name"
    docker rm -f "$container_name" >/dev/null
  fi
}

echo "[info] Project: $PROJECT_NAME"
echo "[info] Compose file: $COMPOSE_FILE_PATH"
echo "[info] Database file: $DB_FILE_PATH"

case "$ACTION" in
  start)
    if [ ! -f "$DB_FILE_PATH" ]; then
      echo "[error] Database file not found: $DB_FILE_PATH" >&2
      echo "[error] Put your existing portfolio.db there, or run with DB_FILE=/path/to/portfolio.db." >&2
      exit 1
    fi

    echo "[info] Stopping previous Docker containers for this project..."
    compose down --remove-orphans
    remove_manual_container "$PROJECT_NAME"
    remove_manual_container "$PROJECT_NAME-web"

    echo "[info] Building and starting Docker containers..."
    compose up -d --build

    echo "[info] Current status:"
    compose ps

    echo "[ok] Started. Visit: http://localhost:5003"
    echo "[ok] View logs: PROJECT_NAME=$PROJECT_NAME COMPOSE_FILE=$COMPOSE_FILE_INPUT sh docker-start.sh logs"
    ;;
  stop)
    echo "[info] Stopping Docker containers for this project..."
    compose down --remove-orphans
    remove_manual_container "$PROJECT_NAME"
    remove_manual_container "$PROJECT_NAME-web"
    echo "[ok] Stopped."
    ;;
  logs)
    compose logs -f
    ;;
  *)
    echo "Usage: sh docker-start.sh [start|stop|logs]" >&2
    exit 1
    ;;
esac
