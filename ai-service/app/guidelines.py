from app.rules import (
    COMBINATION_MATCH_THRESHOLD,
    COMMON_AFFIXES,
    DISALLOWED_WORDS,
    PERIODICITY_MATCH_THRESHOLD,
    PERIODICITY_WORDS,
    TRIVIAL_AFFIX_MATCH_THRESHOLD,
)
from app.schemas import Violation
from app.similarity import best_match, tokenize


def check_disallowed_words(title: str) -> Violation | None:
    tokens = set(tokenize(title))
    hits = sorted(tokens & DISALLOWED_WORDS)
    if not hits:
        return None
    return Violation(
        type="DISALLOWED_WORD",
        message=f"Title contains disallowed word(s): {', '.join(hits)}.",
    )


def check_trivial_affix(title: str, existing_titles: list[str]) -> Violation | None:
    tokens = tokenize(title)
    if len(tokens) < 2:
        return None

    candidates = []
    if tokens[0] in COMMON_AFFIXES:
        candidates.append(" ".join(tokens[1:]))
    if tokens[-1] in COMMON_AFFIXES:
        candidates.append(" ".join(tokens[:-1]))

    for remainder in candidates:
        match_title, score = best_match(remainder, existing_titles)
        if match_title and score >= TRIVIAL_AFFIX_MATCH_THRESHOLD:
            return Violation(
                type="DISALLOWED_AFFIX",
                message=(
                    f"Title is a trivial variation of existing title "
                    f"'{match_title}' formed by adding a common prefix/suffix."
                ),
            )
    return None


def check_combination(title: str, existing_titles: list[str]) -> Violation | None:
    tokens = tokenize(title)
    if len(tokens) < 2:
        return None

    for split in range(1, len(tokens)):
        left = " ".join(tokens[:split])
        right = " ".join(tokens[split:])

        left_title, left_score = best_match(left, existing_titles)
        right_title, right_score = best_match(right, existing_titles)

        if (
            left_title
            and right_title
            and left_title != right_title
            and left_score >= COMBINATION_MATCH_THRESHOLD
            and right_score >= COMBINATION_MATCH_THRESHOLD
        ):
            return Violation(
                type="TITLE_COMBINATION",
                message=(
                    f"Title appears to combine existing titles "
                    f"'{left_title}' and '{right_title}'."
                ),
            )
    return None


def check_periodicity_variation(title: str, existing_titles: list[str]) -> Violation | None:
    tokens = tokenize(title)
    periodicity_tokens = [t for t in tokens if t in PERIODICITY_WORDS]
    if not periodicity_tokens or len(tokens) < 2:
        return None

    remainder = " ".join(t for t in tokens if t not in PERIODICITY_WORDS)
    match_title, score = best_match(remainder, existing_titles)
    if match_title and score >= PERIODICITY_MATCH_THRESHOLD:
        return Violation(
            type="PERIODICITY_MODIFICATION",
            message=(
                f"Title is existing title '{match_title}' with a periodicity "
                f"word added/changed, which is not allowed."
            ),
        )
    return None
