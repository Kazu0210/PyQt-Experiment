import hashlib
import hmac

from core.base_monitor import _read_config, _write_config

DEFAULT_PASSWORD = "password123"


def password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_password_hash() -> str:
    """Return the stored lock hash, creating the default password on first run."""
    config = _read_config()
    lock = config.get("lock")
    stored = lock.get("password_hash") if isinstance(lock, dict) else None
    if isinstance(stored, str) and stored:
        return stored

    digest = password_hash(DEFAULT_PASSWORD)
    config["lock"] = {"password_hash": digest}
    try:
        _write_config(config)
    except OSError as e:
        print(f"Error saving lock password: {e}")
    return digest


def verify_password(password: str, stored_hash: str) -> bool:
    return hmac.compare_digest(password_hash(password), stored_hash)
