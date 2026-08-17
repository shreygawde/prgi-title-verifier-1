import json
from dataclasses import dataclass, field
from pathlib import Path

from app.store import TitleRecord

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "sample_titles.json"


@dataclass
class FakeTitleStore:
    """In-memory stand-in for the real (Postgres + embeddings) TitleStore.

    The real store talks to a live, shared Supabase database, so tests must
    not use it directly -- every verify_title() call writes a permanent
    PENDING_APPLICATION row via add_pending(). This fake implements the same
    interface (candidates/add_pending) purely in memory, off the same
    sample dataset the real DB was seeded from.
    """

    records: list[TitleRecord] = field(default_factory=list)

    def add_pending(self, title: str, language: str, periodicity: str) -> None:
        self.records.append(TitleRecord(title, language, periodicity, "PENDING_APPLICATION"))

    def candidates(self, title: str, limit: int = 100) -> list[TitleRecord]:
        return self.records[:limit]


def load_sample_store() -> FakeTitleStore:
    store = FakeTitleStore()
    with open(DATA_FILE, encoding="utf-8") as f:
        rows = json.load(f)
    for row in rows:
        store.records.append(
            TitleRecord(row["title"], row["language"], row["periodicity"], "REGISTERED")
        )
    return store
