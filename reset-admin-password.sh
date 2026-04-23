#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-iamscor123}"

if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
  PYTHON_BIN="$SCRIPT_DIR/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "[error] Python is not installed." >&2
  exit 1
fi

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
