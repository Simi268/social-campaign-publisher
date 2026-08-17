from fastapi import FastAPI

from app.api.webhooks import router as webhook_router

from app.api.campaigns import router as campaign_router

from app.api.social_posts import router as social_posts_router

app = FastAPI(
    title="Social Campaign Publisher",
    version="0.1.0",
)


app.include_router(webhook_router)
app.include_router(campaign_router)
app.include_router(social_posts_router)


@app.get("/")
def root():
    return {
        "name": "Social Campaign Publisher",
        "status": "ok",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }