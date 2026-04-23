#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-iamscor123}"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"

choose_python() {
  if [ -x "$VENV_PYTHON" ]; then
    PYTHON_BIN="$VENV_PYTHON"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python3)
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python)
  else
    echo "[error] Python is not installed." >&2
    exit 1
  fi
}

python_ready() {
  "$1" - <<'PY' >/dev/null 2>&1
import flask
import flask_cors
import flask_login
import flask_migrate
import flask_sqlalchemy
import werkzeug
PY
}

ensure_dependencies() {
  if python_ready "$PYTHON_BIN"; then
    return
  fi

  echo "[warn] Python dependencies are missing. Preparing local virtualenv..."

  if [ ! -x "$VENV_PYTHON" ]; then
    echo "[info] Creating virtualenv at $SCRIPT_DIR/venv"
    "$PYTHON_BIN" -m venv "$SCRIPT_DIR/venv"
  fi

  PYTHON_BIN="$VENV_PYTHON"
  echo "[info] Installing requirements..."
  "$PYTHON_BIN" -m pip install -r "$SCRIPT_DIR/requirements.txt"
}

choose_python
ensure_dependencies

echo "[info] Resetting admin password..."
echo "[info] Target username: $ADMIN_USERNAME"

"$PYTHON_BIN" - "$ADMIN_USERNAME" "$ADMIN_PASSWORD" <<'PY'
import sys

from werkzeug.security import generate_password_hash

from app import create_app
from app.models import Admin, db


username = sys.argv[1]
password = sys.argv[2]

app = create_app()

with app.app_context():
    db.create_all()

    admin = Admin.query.filter_by(username=username).first()
    if admin is None:
        admin = Admin(
            username=username,
            password_hash=generate_password_hash(password),
        )
        db.session.add(admin)
        action = "created"
    else:
        admin.password_hash = generate_password_hash(password)
        action = "updated"

    db.session.commit()

print(f"[ok] Admin '{username}' {action}.")
print("[ok] Password has been reset to the configured value.")
PY
