"""Encryption utilities for sensitive data."""
import os
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Cache the Fernet instance
_fernet: Optional[Fernet] = None


def get_fernet() -> Fernet:
    """Get or create Fernet encryption instance."""
    global _fernet

    if _fernet is None:
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable not set. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        try:
            _fernet = Fernet(key.encode())
        except Exception as e:
            raise ValueError(f"Invalid ENCRYPTION_KEY: {e}")

    return _fernet


def encrypt_password(password: str) -> str:
    """
    Encrypt a password for storage.

    Args:
        password: Plain text password

    Returns:
        Encrypted password string (base64 encoded)
    """
    if not password:
        return ""

    f = get_fernet()
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted: str) -> str:
    """
    Decrypt a stored password.

    Args:
        encrypted: Encrypted password string

    Returns:
        Plain text password

    Raises:
        ValueError: If decryption fails (wrong key or corrupted data)
    """
    if not encrypted:
        return ""

    f = get_fernet()
    try:
        decrypted = f.decrypt(encrypted.encode())
        return decrypted.decode()
    except InvalidToken:
        logger.error("Failed to decrypt password - invalid token or wrong key")
        raise ValueError("Failed to decrypt password. The encryption key may have changed.")


def is_encrypted(value: str) -> bool:
    """
    Check if a value appears to be encrypted (Fernet format).

    Fernet tokens start with 'gAAAAA' (base64 encoded version byte + timestamp).
    """
    if not value:
        return False
    return value.startswith("gAAAAA")
