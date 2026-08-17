from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CampaignCreate(BaseModel):
    title: str
    source_url: str | None = None
    scheduled_at: datetime | None = None


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_url: str | None
    status: str
    scheduled_at: datetime | None