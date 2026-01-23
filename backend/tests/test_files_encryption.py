"""Tests for token encryption utilities."""
import pytest
from domains.files.encryption import TokenEncryption


@pytest.fixture
def encryption():
    """Create a TokenEncryption instance with a test key."""
    return TokenEncryption("test-encryption-key-for-testing-only")


def test_encrypt_decrypt_roundtrip(encryption: TokenEncryption):
    """Test that encrypt -> decrypt returns original plaintext."""
    plaintext = "this is a secret token"
    encrypted = encryption.encrypt(plaintext)
    decrypted = encryption.decrypt(encrypted)
    
    assert decrypted == plaintext
    assert encrypted != plaintext  # Ensure it's actually encrypted


def test_encrypt_produces_different_ciphertext(encryption: TokenEncryption):
    """Test that encrypting the same plaintext twice produces different results."""
    plaintext = "secret token"
    encrypted1 = encryption.encrypt(plaintext)
    encrypted2 = encryption.encrypt(plaintext)
    
    # Due to random IV, ciphertexts should differ
    assert encrypted1 != encrypted2
    
    # But both should decrypt to the same plaintext
    assert encryption.decrypt(encrypted1) == plaintext
    assert encryption.decrypt(encrypted2) == plaintext


def test_encrypt_empty_string(encryption: TokenEncryption):
    """Test encrypting an empty string."""
    plaintext = ""
    encrypted = encryption.encrypt(plaintext)
    decrypted = encryption.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_encrypt_long_string(encryption: TokenEncryption):
    """Test encrypting a long token."""
    plaintext = "a" * 1000
    encrypted = encryption.encrypt(plaintext)
    decrypted = encryption.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_decrypt_invalid_ciphertext_raises_error(encryption: TokenEncryption):
    """Test that decrypting invalid data raises an exception."""
    with pytest.raises(Exception):
        encryption.decrypt("invalid-base64-data")


def test_different_keys_produce_different_results():
    """Test that different encryption keys produce incompatible results."""
    enc1 = TokenEncryption("key1")
    enc2 = TokenEncryption("key2")
    
    plaintext = "secret"
    encrypted = enc1.encrypt(plaintext)
    
    # Decrypting with a different key should fail
    with pytest.raises(Exception):
        enc2.decrypt(encrypted)


def test_encrypt_special_characters(encryption: TokenEncryption):
    """Test encrypting strings with special characters."""
    plaintext = "token!@#$%^&*()_+={}[]|\\:;\"'<>?,./~`"
    encrypted = encryption.encrypt(plaintext)
    decrypted = encryption.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_encrypt_unicode(encryption: TokenEncryption):
    """Test encrypting Unicode strings."""
    plaintext = "🔐 secret token 密碼 🔑"
    encrypted = encryption.encrypt(plaintext)
    decrypted = encryption.decrypt(encrypted)
    
    assert decrypted == plaintext
