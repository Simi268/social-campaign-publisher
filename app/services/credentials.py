from sqlalchemy.orm import Session

from app.models.platform_credential import PlatformCredential
from app.security.token_encryption import TokenEncryption


class CredentialService:
    def __init__(self, encryption: TokenEncryption | None = None):
        self.encryption = encryption or TokenEncryption()

    def save_token(
        self,
        db: Session,
        platform: str,
        access_token: str,
    ) -> PlatformCredential:
        encrypted_token = self.encryption.encrypt(access_token)

        credential = (
            db.query(PlatformCredential)
            .filter(
                PlatformCredential.platform == platform
            )
            .first()
        )

        if credential is None:
            credential = PlatformCredential(
                platform=platform,
                encrypted_access_token=encrypted_token,
            )
            db.add(credential)
        else:
            credential.encrypted_access_token = encrypted_token

        db.commit()
        db.refresh(credential)

        return credential

    def get_token(
        self,
        db: Session,
        platform: str,
    ) -> str:
        credential = (
            db.query(PlatformCredential)
            .filter(
                PlatformCredential.platform == platform
            )
            .first()
        )

        if credential is None:
            raise ValueError(
                f"No credentials configured for {platform}"
            )

        return self.encryption.decrypt(
            credential.encrypted_access_token
        )