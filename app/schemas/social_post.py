from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SocialPostCreate(BaseModel):
    platform: str
    caption: str
    image_path: str | None = None
    scheduled_at: datetime | None = None


class SocialPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    platform: str
    caption: str
    image_path: str | None
    status: str
    external_post_id: str | None
    idempotency_key: str
    scheduled_at: datetime | None
    published_at: datetime | None