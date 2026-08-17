from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.engine import verify_title
from app.schemas import (
    SimilarityMatch,
    SimilarityRequest,
    SimilarityResponse,
    VerifyRequest,
    VerifyResponse,
)
from app.similarity import fuzzy_signal, phonetic_signal
from app.store import title_store


app = FastAPI(
    title="PRGI Title Verification AI Service",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "prgi-ai-service"
    }


@app.post("/analyze", response_model=VerifyResponse)
def analyze_title(payload: VerifyRequest):
    return verify_title(
        payload.title,
        payload.language,
        payload.periodicity,
        title_store,
        application_number=payload.application_number,
    )


@app.post("/similarity", response_model=SimilarityResponse)
def check_similarity(payload: SimilarityRequest):
    matches = [
        SimilarityMatch(
            title=candidate,
            fuzzy=fuzzy_signal(payload.title, candidate),
            phonetic=phonetic_signal(payload.title, candidate),
        )
        for candidate in payload.candidates
    ]
    return SimilarityResponse(matches=matches)