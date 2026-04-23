#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

ADMIN_USERNAME="${1:-${ADMIN_USERNAME:-admin}}"
ADMIN_PASSWORD="${2:-${ADMIN_PASSWORD:-iamscor123}}"

choose_python() {
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python3)
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python)
  else
    echo "[error] Python is not installed." >&2
    exit 1
  fi
}

choose_python

echo "[info] Resetting admin password..."
echo "[info] Target username: $ADMIN_USERNAME"

"$PYTHON_BIN" - "$SCRIPT_DIR" "$ADMIN_USERNAME" "$ADMIN_PASSWORD" <<'PY'
import datetime
import hashlib
import os
import secrets
import sqlite3
import string
import sys


script_dir = sys.argv[1]
username = sys.argv[2]
password = sys.argv[3]


def resolve_database_path(root_dir: str) -> str:
    db_path_override = os.environ.get("DB_PATH", "").strip()
    if db_path_override:
        if os.path.isabs(db_path_override):
            return db_path_override
        return os.path.join(root_dir, db_path_override)

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        return os.path.join(root_dir, "instance", "portfolio.db")

    if not database_url.startswith("sqlite:///"):
        raise SystemExit(
            "[error] This script only supports SQLite databases. "
            "Set DB_PATH to your sqlite file path before running."
        )

    sqlite_path = database_url[len("sqlite:///"):]
    if os.path.isabs(sqlite_path):
        return sqlite_path
    return os.path.join(root_dir, sqlite_path)


def generate_password_hash(raw_password: str) -> str:
    salt_chars = string.ascii_letters + string.digits
    salt = "".join(secrets.choice(salt_chars) for _ in range(16))
    digest = hashlib.scrypt(
        raw_password.encode("utf-8"),
        salt=salt.encode("utf-8"),
        n=32768,
        r=8,
        p=1,
        maxmem=64 * 1024 * 1024,
    ).hex()
    return f"scrypt:32768:8:1${salt}${digest}"


db_path = resolve_database_path(script_dir)
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)
try:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at DATETIME
        )
        """
    )

    password_hash = generate_password_hash(password)
    existing = conn.execute(
        "SELECT id FROM admins WHERE username = ?",
        (username,),
    ).fetchone()

    if existing is None:
        conn.execute(
            "INSERT INTO admins (username, password_hash, created_at) VALUES (?, ?, ?)",
            (
                username,
                password_hash,
                datetime.datetime.utcnow().isoformat(sep=" "),
            ),
        )
        action = "created"
    else:
        conn.execute(
            "UPDATE admins SET password_hash = ? WHERE username = ?",
            (password_hash, username),
        )
        action = "updated"

    conn.commit()
finally:
    conn.close()

print(f"[ok] Database: {db_path}")
print(f"[ok] Admin '{username}' {action}.")
print("[ok] Password has been reset to the configured value.")
PY
