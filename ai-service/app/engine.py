import re

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


def verify_title(
    title: str,
    language: str,
    periodicity: str,
    store: TitleStore,
    application_number: str | None = None,
) -> VerifyResponse:

    candidates = store.candidates(
        title,
        application_number=application_number,
    )

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

    # Extract titles explicitly referenced by guideline violations.
    #
    # Example:
    # "Title is a trivial variation of existing title 'Gujarat Samachar'..."
    #
    # This lets us show legitimate registered evidence even if the
    # similarity score itself is low because generic words are deliberately
    # down-weighted.
    guideline_titles: set[str] = set()

    for violation in violations:
        referenced_titles = re.findall(
            r"'([^']+)'",
            violation.message,
        )

        guideline_titles.update(referenced_titles)

    scored_matches: list[MatchResult] = []
    top_similarity = 0.0

    for record in candidates:
        result = compare_titles(title, record.title)

        if result.score > top_similarity:
            top_similarity = result.score

        should_display = result.score >= SIMILARITY_DISPLAY_THRESHOLD

        # If a registered title directly triggered a guideline violation,
        # expose it as evidence even when its raw similarity is below the
        # normal display threshold.
        is_guideline_evidence = (
            record.source == "REGISTERED"
            and record.title in guideline_titles
        )

        if should_display or is_guideline_evidence:
            match_types = list(result.match_types)

            if is_guideline_evidence and not match_types:
                match_types = ["GUIDELINE_MATCH"]

            scored_matches.append(
                MatchResult(
                    title=record.title,
                    score=result.score,
                    match_types=match_types,
                    language=record.language,
                    periodicity=record.periodicity,
                    source=record.source,
                )
            )

    scored_matches.sort(
        key=lambda m: m.score,
        reverse=True,
    )

    scored_matches = scored_matches[:TOP_MATCHES_LIMIT]

    verification_score = round(
        max(0.0, 100.0 - top_similarity),
        2,
    )

    has_hard_violation = bool(violations)

    is_too_similar = (
        top_similarity >= SIMILARITY_REJECT_THRESHOLD
    )

    if has_hard_violation or is_too_similar:
        status = "REJECTED"

        if has_hard_violation:
            verification_score = min(
                verification_score,
                15.0,
            )

        if is_too_similar and not has_hard_violation:
            best_match = (
                scored_matches[0]
                if scored_matches
                else None
            )

            violations.append(
                Violation(
                    type="SIMILARITY",
                    message=(
                        f"Title is too similar ({top_similarity:.0f}% match) "
                        f"to an existing title '{best_match.title}'."
                    )
                    if best_match
                    else (
                        "Title is too similar to an existing title."
                    ),
                )
            )

    elif verification_score >= 60:
        status = "LIKELY_ELIGIBLE"

    else:
        status = "NEEDS_REVIEW"

    explanation = _build_explanation(
        status,
        violations,
        scored_matches,
    )

    # Store/update the application only AFTER verification.
    store.add_pending(
        title,
        language,
        periodicity,
        application_number=application_number,
    )

    return VerifyResponse(
        title=title,
        status=status,
        verification_score=verification_score,
        violations=violations,
        matches=scored_matches,
        explanation=explanation,
    )


def _build_explanation(
    status: str,
    violations: list[Violation],
    matches: list[MatchResult],
) -> str:

    if violations:
        return " ".join(
            v.message
            for v in violations
        )

    if matches:
        top = matches[0]

        return (
            f"Highest similarity is {top.score:.0f}% "
            f"against '{top.title}' "
            f"({', '.join(top.match_types)})."
        )

    return (
        "No significant similarity or guideline "
        "violations found."
    )