import os
from dataclasses import dataclass
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")


@dataclass
class TitleRecord:
    title: str
    language: str
    periodicity: str
    source: str  # "REGISTERED" or "PENDING_APPLICATION"


class TitleStore:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def add_pending(self, title: str, language: str, periodicity: str) -> None:
        """Record a new title application.

        Pending applications live in public.applications, not
        public.prgi_titles. That table holds the authoritative registered
        title registry only; applications are tracked separately with their
        own status (PENDING/APPROVED/REJECTED/WITHDRAWN).
        """
        if not DATABASE_URL:
            return

        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.applications
                    (proposed_title, language, periodicity, status)
                    VALUES (%s, %s, %s, 'PENDING')
                    """,
                    (title, language, periodicity)
                )

    def candidates(self, title: str, limit: int = 100) -> list[TitleRecord]:
        """Return candidate titles to compare the proposed title against.

        Combines two sources:
          - public.prgi_titles: the registered title registry, ranked by
            pgvector embedding similarity (unchanged from before).
          - public.applications: pending applications. These have no
            embedding column (out of scope for this MVP), so they are
            fetched directly and left for the existing fuzzy/phonetic
            compare_titles() flow in engine.py to score.
        """
        if not DATABASE_URL:
            return []

        embedding = self.model.encode(title).tolist()
        records: list[TitleRecord] = []
        seen: set[tuple[str, str, str]] = set()

        with psycopg.connect(DATABASE_URL) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT title, language, periodicity
                    FROM public.prgi_titles
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (str(embedding), limit)
                )
                for row in cur.fetchall():
                    key = (row[0].strip().lower(), row[1], row[2])
                    if key in seen:
                        continue
                    seen.add(key)
                    records.append(
                        TitleRecord(title=row[0], language=row[1], periodicity=row[2], source="REGISTERED")
                    )

                cur.execute(
                    """
                    SELECT proposed_title, language, periodicity
                    FROM public.applications
                    WHERE status = 'PENDING'
                    LIMIT %s
                    """,
                    (limit,)
                )
                for row in cur.fetchall():
                    key = (row[0].strip().lower(), row[1], row[2])
                    if key in seen:
                        continue
                    seen.add(key)
                    records.append(
                        TitleRecord(title=row[0], language=row[1], periodicity=row[2], source="PENDING_APPLICATION")
                    )

        return records


title_store = TitleStore()