from fastapi import FastAPI

app = FastAPI(
    title="Social Campaign Publisher",
    version="0.1.0",
)


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