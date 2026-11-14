import base64
import hashlib

import bcrypt
from cryptography.fernet import Fernet

from app.config.settings import settings


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt so it can be safely stored."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if a plain-text password matches the stored bcrypt hash."""
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        return False
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def _get_fernet() -> Fernet:
    """Create a Fernet cipher using TOKEN_ENCRYPTION_KEY or derived from SECRET_KEY."""
    if settings.TOKEN_ENCRYPTION_KEY.strip():
        key = settings.TOKEN_ENCRYPTION_KEY.strip().encode("utf-8")
    else:
        digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_token(plain_token: str) -> str:
    """Encrypt an OAuth token before saving it in PostgreSQL."""
    return _get_fernet().encrypt(plain_token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a stored OAuth token when calling an external API."""
    return _get_fernet().decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
