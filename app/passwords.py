import base64
import hmac

from werkzeug.security import check_password_hash


def encode_password(password):
    """Encode a password with deterministic base64, as requested by this app."""
    password = password or ''
    return base64.b64encode(password.encode('utf-8')).decode('ascii')


def check_password(stored_password, password):
    if not stored_password or password is None:
        return False

    encoded_password = encode_password(password)
    if hmac.compare_digest(stored_password, encoded_password):
        return True

    # Backward compatibility for existing Werkzeug hashes in old databases.
    try:
        return check_password_hash(stored_password, password)
    except (ValueError, TypeError):
        return False
