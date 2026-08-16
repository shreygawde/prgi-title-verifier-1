from fastapi import FastAPI

from app.engine import verify_title
from app.schemas import VerifyRequest, VerifyResponse
from app.store import title_store

app = FastAPI(
    title="PRGI Title Verification AI Service",
    version="0.1.0"
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "prgi-ai-service"
    }


@app.post("/analyze", response_model=VerifyResponse)
def analyze_title(payload: VerifyRequest):
    return verify_title(payload.title, payload.language, payload.periodicity, title_store)