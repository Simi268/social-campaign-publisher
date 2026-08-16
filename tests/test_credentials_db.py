from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.platform_credential import PlatformCredential
from app.services.credentials import CredentialService
from app.security.token_encryption import TokenEncryption


def test_platform_credential_is_stored_encrypted():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    encryption = TokenEncryption(
        Fernet.generate_key().decode()
    )

    service = CredentialService(encryption)

    plaintext_token = "fake-access-token"

    service.save_token(
        db=db,
        platform="instagram",
        access_token=plaintext_token,
    )

    row = db.query(PlatformCredential).filter(
        PlatformCredential.platform == "instagram"
    ).first()

    assert row is not None
    assert row.encrypted_access_token != plaintext_token
    assert encryption.decrypt(
        row.encrypted_access_token
    ) == plaintext_token

    db.close()
    engine.dispose()