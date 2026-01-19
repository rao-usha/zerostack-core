"""
Encryption utilities for securely storing OAuth tokens
"""
import os
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class TokenEncryption:
    """
    Handles encryption/decryption of OAuth tokens using Fernet (symmetric encryption)
    """
    
    def __init__(self, encryption_key: str):
        """
        Initialize with encryption key from environment
        
        Args:
            encryption_key: Base key for deriving Fernet key
        """
        # Derive a proper Fernet key from the provided key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'nex_files_salt_v1',  # Static salt for consistent key derivation
            iterations=100000,
        )
        key_bytes = kdf.derive(encryption_key.encode())
        fernet_key = b64encode(key_bytes)
        self.cipher = Fernet(fernet_key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return b64encode(encrypted_bytes).decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            ciphertext: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""
        
        encrypted_bytes = b64decode(ciphertext.encode('utf-8'))
        decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')


def get_token_encryptor() -> TokenEncryption:
    """
    Get a TokenEncryption instance using the configured encryption key
    
    Returns:
        TokenEncryption instance
    """
    encryption_key = os.getenv('ENCRYPTION_KEY') or os.getenv('SECRET_KEY')
    if not encryption_key:
        raise ValueError(
            "ENCRYPTION_KEY or SECRET_KEY must be set in environment for token encryption"
        )
    return TokenEncryption(encryption_key)
