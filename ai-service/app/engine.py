from app.guidelines import (
    check_combination,
    check_disallowed_words,
    check_periodicity_variation,
    check_trivial_affix,
)
from app.rules import SIMILARITY_DISPLAY_THRESHOLD, SIMILARITY_REJECT_THRESHOLD
from app.schemas import MatchResult, VerifyResponse, Violation
from app.similarity import compare_titles
from app.store import TitleStore

TOP_MATCHES_LIMIT = 5


def verify_title(title: str, language: str, periodicity: str, store: TitleStore) -> VerifyResponse:
    candidates = store.candidates(title)
    candidate_titles = [c.title for c in candidates]

    violations: list[Violation] = []
    for check in (
        lambda: check_disallowed_words(title),
        lambda: check_trivial_affix(title, candidate_titles),
        lambda: check_combination(title, candidate_titles),
        lambda: check_periodicity_variation(title, candidate_titles),
    ):
        result = check()
        if result:
            violations.append(result)

    scored_matches: list[MatchResult] = []
    top_similarity = 0.0
    for record in candidates:
        result = compare_titles(title, record.title)
        if result.score > top_similarity:
            top_similarity = result.score
        if result.score >= SIMILARITY_DISPLAY_THRESHOLD:
            scored_matches.append(
                MatchResult(
                    title=record.title,
                    score=result.score,
                    match_types=result.match_types,
                    language=record.language,
                    periodicity=record.periodicity,
                    source=record.source,
                )
            )

    scored_matches.sort(key=lambda m: m.score, reverse=True)
    scored_matches = scored_matches[:TOP_MATCHES_LIMIT]

    verification_score = round(max(0.0, 100.0 - top_similarity), 2)

    has_hard_violation = bool(violations)
    is_too_similar = top_similarity >= SIMILARITY_REJECT_THRESHOLD

    if has_hard_violation or is_too_similar:
        status = "REJECTED"
        verification_score = min(verification_score, 15.0) if has_hard_violation else verification_score
        if is_too_similar and not has_hard_violation:
            violations.append(
                Violation(
                    type="SIMILARITY",
                    message=(
                        f"Title is too similar ({top_similarity:.0f}% match) to an "
                        f"existing title '{scored_matches[0].title}'."
                    )
                    if scored_matches
                    else "Title is too similar to an existing title.",
                )
            )
    elif verification_score >= 60:
        status = "LIKELY_ELIGIBLE"
    else:
        status = "NEEDS_REVIEW"

    explanation = _build_explanation(status, violations, scored_matches)

    store.add_pending(title, language, periodicity)

    return VerifyResponse(
        title=title,
        status=status,
        verification_score=verification_score,
        violations=violations,
        matches=scored_matches,
        explanation=explanation,
    )


def _build_explanation(status: str, violations: list[Violation], matches: list[MatchResult]) -> str:
    if violations:
        return " ".join(v.message for v in violations)
    if matches:
        top = matches[0]
        return (
            f"Highest similarity is {top.score:.0f}% against '{top.title}' "
            f"({', '.join(top.match_types)})."
        )
    return "No significant similarity or guideline violations found."
