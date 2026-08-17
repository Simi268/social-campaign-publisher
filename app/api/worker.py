from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.workers.publisher import PublisherWorker


router = APIRouter(
    prefix="/worker",
    tags=["worker"],
)


@router.post("/publish-due")
def publish_due_posts(
    db: Session = Depends(get_db),
):
    worker = PublisherWorker()

    results = worker.publish_due_posts(db)

    return {
        "status": "completed",
        "published_count": len(results),
        "posts": [
            {
                "external_post_id": result.external_post_id,
                "status": result.status,
            }
            for result in results
        ],
    }