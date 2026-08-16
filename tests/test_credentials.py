from cryptography.fernet import Fernet

from app.security.token_encryption import TokenEncryption


def test_credential_encryption_round_trip():
    key = Fernet.generate_key().decode()
    encryption = TokenEncryption(key)

    plaintext = "fake-access-token"

    encrypted = encryption.encrypt(plaintext)

    assert encrypted != plaintext
    assert encryption.decrypt(encrypted) == plaintext