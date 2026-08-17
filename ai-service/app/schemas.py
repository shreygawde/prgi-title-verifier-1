from pydantic import BaseModel


class VerifyRequest(BaseModel):
    title: str
    language: str
    periodicity: str


class Violation(BaseModel):
    type: str
    message: str


class MatchResult(BaseModel):
    title: str
    score: float
    match_types: list[str]
    language: str
    periodicity: str
    source: str


class VerifyResponse(BaseModel):
    title: str
    status: str
    verification_score: float
    violations: list[Violation]
    matches: list[MatchResult]
    explanation: str


class SimilarityRequest(BaseModel):
    title: str
    candidates: list[str]


class SimilarityMatch(BaseModel):
    title: str
    fuzzy: float
    phonetic: float


class SimilarityResponse(BaseModel):
    matches: list[SimilarityMatch]
