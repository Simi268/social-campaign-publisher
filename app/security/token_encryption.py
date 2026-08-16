from cryptography.fernet import Fernet

from app.core.database import settings


class TokenEncryption:
    def __init__(self, key: str | None = None):
        key = key or settings.token_encryption_key

        self._fernet = Fernet(key.encode())

    def encrypt(self, token: str) -> str:
        if not token:
            raise ValueError("Token cannot be empty.")

        return self._fernet.encrypt(
            token.encode()
        ).decode()

    def decrypt(self, encrypted_token: str) -> str:
        if not encrypted_token:
            raise ValueError(
                "Encrypted token cannot be empty."
            )

        return self._fernet.decrypt(
            encrypted_token.encode()
        ).decode()