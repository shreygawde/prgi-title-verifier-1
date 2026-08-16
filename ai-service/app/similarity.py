import re

import jellyfish
from rapidfuzz import fuzz

from app.rules import COMMON_AFFIXES, CROSS_LANGUAGE_EQUIVALENTS
#very imp&basic thing, this is used to match words in a string, ignoring punctuation and special characters. It will find sequences of alphabetic characters (both uppercase and lowercase) and return them as a list of words.
_WORD_RE = re.compile(r"[a-zA-Z]+")


def normalize(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def tokenize(text: str) -> list[str]:
    return normalize(text).split()


def strip_affixes(tokens: list[str]) -> list[str]:
    core = [t for t in tokens if t not in COMMON_AFFIXES]
    return core or tokens


def canonicalize(tokens: list[str]) -> list[str]:
    return [CROSS_LANGUAGE_EQUIVALENTS.get(t, t) for t in tokens]


def _phonetic_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    soundex_match = 100.0 if jellyfish.soundex(a) == jellyfish.soundex(b) else 0.0
    metaphone_score = fuzz.ratio(jellyfish.metaphone(a), jellyfish.metaphone(b))
    return max(soundex_match, metaphone_score)


class SimilarityResult:
    def __init__(self, score: float, match_types: list[str]):
        self.score = round(score, 2)
        self.match_types = match_types


def compare_titles(new_title: str, existing_title: str) -> SimilarityResult:
    new_tokens = tokenize(new_title)
    exist_tokens = tokenize(existing_title)

    raw_new, raw_exist = " ".join(new_tokens), " ".join(exist_tokens)
    raw_score = fuzz.token_sort_ratio(raw_new, raw_exist)

    core_new = " ".join(strip_affixes(new_tokens))
    core_exist = " ".join(strip_affixes(exist_tokens))
    core_score = fuzz.token_sort_ratio(core_new, core_exist)

    canon_new = " ".join(strip_affixes(canonicalize(new_tokens)))
    canon_exist = " ".join(strip_affixes(canonicalize(exist_tokens)))
    canon_score = fuzz.token_sort_ratio(canon_new, canon_exist)

    phonetic_score = _phonetic_score(
        core_new.replace(" ", ""), core_exist.replace(" ", "")
    )

    match_types = []
    if raw_score >= 90:
        match_types.append("EXACT_OR_NEAR_EXACT")
    if core_score >= 80 and core_score > raw_score:
        match_types.append("AFFIX_STRIPPED")
    if phonetic_score >= 80:
        match_types.append("PHONETIC")
    if canon_score >= 80 and canon_score > max(raw_score, core_score):
        match_types.append("CROSS_LANGUAGE_MEANING")
    if not match_types and max(raw_score, core_score, canon_score, phonetic_score) >= 60:
        match_types.append("FUZZY")

    final_score = max(raw_score, core_score, canon_score, phonetic_score)
    return SimilarityResult(final_score, match_types)


def best_match(text: str, candidates: list[str]) -> tuple[str | None, float]:
    best_title, best_score = None, 0.0
    norm_text = normalize(text)
    if not norm_text:
        return None, 0.0
    for candidate in candidates:
        score = fuzz.token_set_ratio(norm_text, normalize(candidate))
        if score > best_score:
            best_title, best_score = candidate, score
    return best_title, best_score
