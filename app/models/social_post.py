from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SocialPost(Base):
    __tablename__ = "social_posts"

    id: Mapped[int] = mapped_column(primary_key=True)

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )

    platform: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    caption: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    image_path: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DRAFT",
    )

    external_post_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    campaign = relationship(
        "Campaign",
        back_populates="social_posts",
    )

    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "platform",
            name="uq_campaign_platform",
        ),
        UniqueConstraint(
            "idempotency_key",
            name="uq_social_post_idempotency_key",
        ),
        Index(
            "ix_social_posts_status_scheduled_at",
            "status",
            "scheduled_at",
        ),
    )