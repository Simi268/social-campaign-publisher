from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campaign import Campaign
from app.schemas.campaign import (
    CampaignCreate,
    CampaignResponse,
)
from app.workers.publisher import PublisherWorker


router = APIRouter(
    prefix="/campaigns",
    tags=["campaigns"],
)


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=201,
)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
):
    campaign = Campaign(
        title=payload.title,
        source_url=payload.source_url,
        scheduled_at=payload.scheduled_at,
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    return campaign


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    return campaign


@router.post(
    "/{campaign_id}/publish",
)
def publish_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    worker = PublisherWorker()

    results = worker.publish_due_posts(
        db,
        campaign_id=campaign_id,
    )

    campaign.status = (
        "PUBLISHED"
        if results
        else "SCHEDULED"
    )

    db.commit()

    return {
        "campaign_id": campaign.id,
        "status": campaign.status,
        "published_count": len(results),
        "posts": [
            {
                "external_post_id": result.external_post_id,
                "status": result.status,
            }
            for result in results
        ],
    }