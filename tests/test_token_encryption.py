from cryptography.fernet import Fernet

from app.security.token_encryption import TokenEncryption


def test_token_can_be_encrypted_and_decrypted():
    key = Fernet.generate_key().decode()

    encryption = TokenEncryption(key)

    token = "fake-access-token"

    encrypted = encryption.encrypt(token)

    assert encrypted != token
    assert encryption.decrypt(encrypted) == token


def test_same_token_produces_different_ciphertext():
    key = Fernet.generate_key().decode()

    encryption = TokenEncryption(key)

    token = "fake-access-token"

    first = encryption.encrypt(token)
    second = encryption.encrypt(token)

    assert first != second