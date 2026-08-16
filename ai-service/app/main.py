from fastapi import FastAPI

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

@app.post("/analyze")
def analyze_title(payload: dict):
    title = payload.get("title", "")

    return {
        "title": title,
        "verification_score": 100,
        "status": "LIKELY_ELIGIBLE",
        "violations": [],
        "matches": []
    }