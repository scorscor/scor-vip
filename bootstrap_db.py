import os
import time

from sqlalchemy.exc import OperationalError

from app import create_app
from app.models import db


def bootstrap_database():
    app = create_app()
    retries = int(os.environ.get('DB_INIT_RETRIES', '10'))
    delay_seconds = int(os.environ.get('DB_INIT_DELAY', '3'))

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            with app.app_context():
                db.create_all()
            print(f"[bootstrap] database is ready on attempt {attempt}")
            return
        except OperationalError as exc:
            last_error = exc
            print(f"[bootstrap] database init failed on attempt {attempt}/{retries}: {exc}")
            if attempt < retries:
                time.sleep(delay_seconds)

    raise last_error


if __name__ == '__main__':
    bootstrap_database()
