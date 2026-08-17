import re

import jellyfish
from metaphone import doublemetaphone
from rapidfuzz import fuzz

from app.rules import (
    COMMON_AFFIXES,
    CROSS_LANGUAGE_EQUIVALENTS,
    GENERIC_PUBLICATION_TERMS,
    SIMILARITY_DISPLAY_THRESHOLD,
)


_WORD_RE = re.compile(r"[a-zA-Z]+")
_GENERIC_TERM_WEIGHT = 0.2
_WORD_FUZZY_CUTOFF = 70.0


def normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def tokenize(text: str) -> list[str]:
    return normalize(text).split()


def strip_affixes(tokens: list[str]) -> list[str]:
    core = [token for token in tokens if token not in COMMON_AFFIXES]
    return core or tokens


def canonicalize(tokens: list[str]) -> list[str]:
    return [CROSS_LANGUAGE_EQUIVALENTS.get(token, token) for token in tokens]


def _term_weight(token: str) -> float:
    return _GENERIC_TERM_WEIGHT if token in GENERIC_PUBLICATION_TERMS else 1.0


def _weighted_word_score(left: list[str], right: list[str], pair_score) -> float:
    """Return one-to-one word correspondence, with generic terms downweighted."""
    if not left or not right:
        return 0.0

    denominator = max(sum(_term_weight(token) for token in left), sum(_term_weight(token) for token in right))
    remaining_right = set(range(len(right)))
    evidence = 0.0

    for left_index in sorted(range(len(left)), key=lambda index: _term_weight(left[index]), reverse=True):
        best_index = None
        best_score = 0.0
        for right_index in remaining_right:
            score = pair_score(left[left_index], right[right_index])
            if score > best_score:
                best_index = right_index
                best_score = score
        if best_index is None or best_score == 0:
            continue
        remaining_right.remove(best_index)
        evidence += min(_term_weight(left[left_index]), _term_weight(right[best_index])) * (best_score / 100.0)

    return 100.0 * evidence / denominator if denominator else 0.0


def _fuzzy_word_score(left: str, right: str) -> float:
    score = fuzz.ratio(left, right)
    return score if score >= _WORD_FUZZY_CUTOFF else 0.0


def _word_phonetic_score(left: str, right: str) -> float:
    """Use equivalent phonetic encodings for individual words only.

    Metaphone codes are intentionally not fuzzily compared: short lossy codes
    can look similar even when the underlying words are unrelated.
    """
    if not left or not right:
        return 0.0
    if left == right or jellyfish.soundex(left) == jellyfish.soundex(right):
        return 100.0

    left_codes = {code for code in doublemetaphone(left) if code}
    right_codes = {code for code in doublemetaphone(right) if code}
    return 100.0 if left_codes & right_codes else 0.0


def _phonetic_score(left: list[str], right: list[str]) -> tuple[float, bool]:
    score = _weighted_word_score(left, right, _word_phonetic_score)
    has_distinctive_pair = any(
        left_token not in GENERIC_PUBLICATION_TERMS
        and right_token not in GENERIC_PUBLICATION_TERMS
        and _word_phonetic_score(left_token, right_token) == 100.0
        for left_token in left
        for right_token in right
    )
    return score, has_distinctive_pair


def _guideline_phonetic_score(left: list[str], right: list[str]) -> float:
    """Word-level phonetic coverage for prescriptive guideline checks."""
    left = [token for token in left if token != "the"]
    right = [token for token in right if token != "the"]
    if not left or not right:
        return 0.0

    unmatched_right = set(range(len(right)))
    matched = 0
    for left_token in left:
        right_index = next(
            (
                index
                for index in unmatched_right
                if _word_phonetic_score(left_token, right[index]) == 100.0
            ),
            None,
        )
        if right_index is not None:
            unmatched_right.remove(right_index)
            matched += 1
    return 100.0 * matched / max(len(left), len(right))


class SimilarityResult:
    def __init__(self, score: float, match_types: list[str]):
        self.score = round(score, 2)
        self.match_types = match_types


def compare_titles(new_title: str, existing_title: str) -> SimilarityResult:
    new_tokens = tokenize(new_title)
    existing_tokens = tokenize(existing_title)
    normalized_new, normalized_existing = " ".join(new_tokens), " ".join(existing_tokens)
    raw_score = fuzz.token_sort_ratio(normalized_new, normalized_existing)

    lexical_score = _weighted_word_score(new_tokens, existing_tokens, _fuzzy_word_score)
    core_new_tokens = strip_affixes(new_tokens)
    core_existing_tokens = strip_affixes(existing_tokens)
    core_score = _weighted_word_score(core_new_tokens, core_existing_tokens, _fuzzy_word_score)

    canonical_new_tokens = strip_affixes(canonicalize(new_tokens))
    canonical_existing_tokens = strip_affixes(canonicalize(existing_tokens))
    canonical_score = _weighted_word_score(
        canonical_new_tokens, canonical_existing_tokens, _fuzzy_word_score
    )
    phonetic_score, has_distinctive_phonetic_pair = _phonetic_score(
        core_new_tokens, core_existing_tokens
    )

    is_exact_duplicate = bool(normalized_new) and normalized_new == normalized_existing
    final_score = 100.0 if is_exact_duplicate else max(
        lexical_score, core_score, canonical_score, phonetic_score
    )

    match_types: list[str] = []
    if is_exact_duplicate or raw_score >= 90:
        match_types.append("EXACT_OR_NEAR_EXACT")
    if core_score >= 80 and core_score > lexical_score:
        match_types.append("AFFIX_STRIPPED")
    if phonetic_score >= 80 and has_distinctive_phonetic_pair:
        match_types.append("PHONETIC")
    if canonical_score >= 80 and canonical_score > max(lexical_score, core_score):
        match_types.append("CROSS_LANGUAGE_MEANING")
    if not match_types and final_score >= SIMILARITY_DISPLAY_THRESHOLD:
        match_types.append("FUZZY")

    return SimilarityResult(final_score, match_types)


def fuzzy_signal(left: str, right: str) -> float:
    return round(fuzz.ratio(normalize(left), normalize(right)) / 100, 4)


def phonetic_signal(left: str, right: str) -> float:
    score, _ = _phonetic_score(tokenize(left), tokenize(right))
    return round(score / 100, 4)


def best_match(text: str, candidates: list[str]) -> tuple[str | None, float]:
    normalized_text = normalize(text)
    if not normalized_text:
        return None, 0.0

    best_title, best_score = None, 0.0
    for candidate in candidates:
        # Subset matching belongs only to guideline checks (for example,
        # "Indian Express" against "The Indian Express"); it is not used by
        # compare_titles(), where generic terms must remain weak evidence.
        score = max(
            compare_titles(text, candidate).score,
            fuzz.token_set_ratio(normalized_text, normalize(candidate)),
            _guideline_phonetic_score(tokenize(text), tokenize(candidate)),
        )
        if score > best_score:
            best_title, best_score = candidate, score
    return best_title, best_score
