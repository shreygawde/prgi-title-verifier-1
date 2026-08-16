import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import jellyfish

from app.similarity import tokenize

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "sample_titles.json"

# Candidate-pruning threshold: below this corpus size a full scan is cheap
# enough that indexing overhead isn't worth it. Above it, only titles
# sharing a first-letter or first-token-soundex bucket with the query are
# compared. This stands in for the DB-side indexing (trigram/soundex
# index) that will replace it once titles live in Postgres.
FULL_SCAN_LIMIT = 500


@dataclass
class TitleRecord:
    title: str
    language: str
    periodicity: str
    source: str  # "REGISTERED" or "PENDING_APPLICATION"


@dataclass
class TitleStore:
    records: list[TitleRecord] = field(default_factory=list)
    _first_letter_index: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))
    _soundex_index: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))

    def _index(self, idx: int, title: str) -> None:
        tokens = tokenize(title)
        if not tokens:
            return
        first_word = tokens[0]
        self._first_letter_index[first_word[0]].append(idx)
        self._soundex_index[jellyfish.soundex(first_word)].append(idx)

    def add(self, title: str, language: str, periodicity: str, source: str) -> None:
        self.records.append(TitleRecord(title, language, periodicity, source))
        self._index(len(self.records) - 1, title)

    def add_pending(self, title: str, language: str, periodicity: str) -> None:
        self.add(title, language, periodicity, source="PENDING_APPLICATION")

    def all_titles(self) -> list[str]:
        return [r.title for r in self.records]

    def candidates(self, title: str) -> list[TitleRecord]:
        if len(self.records) <= FULL_SCAN_LIMIT:
            return list(self.records)

        tokens = tokenize(title)
        if not tokens:
            return list(self.records)
        first_word = tokens[0]
        idxs = set(self._first_letter_index.get(first_word[0], []))
        idxs |= set(self._soundex_index.get(jellyfish.soundex(first_word), []))
        return [self.records[i] for i in idxs]


def load_sample_store() -> TitleStore:
    store = TitleStore()
    with open(DATA_FILE, encoding="utf-8") as f:
        rows = json.load(f)
    for row in rows:
        store.add(row["title"], row["language"], row["periodicity"], source="REGISTERED")
    return store


title_store = load_sample_store()
