from fastapi import FastAPI

from app.api.webhooks import router as webhook_router


app = FastAPI(
    title="Social Campaign Publisher",
    version="0.1.0",
)


app.include_router(webhook_router)


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