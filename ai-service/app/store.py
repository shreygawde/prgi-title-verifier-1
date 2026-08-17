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
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def add_pending(
        self,
        title: str,
        language: str,
        periodicity: str,
        application_number: str | None = None,
    ) -> None:
        """Create or update a pending application."""

        if not DATABASE_URL:
            return

        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                if application_number:
                    cur.execute(
                        """
                        INSERT INTO public.applications
                        (
                            application_number,
                            proposed_title,
                            language,
                            periodicity,
                            status
                        )
                        VALUES (%s, %s, %s, %s, 'PENDING')
                        ON CONFLICT (application_number)
                        DO UPDATE SET
                            proposed_title = EXCLUDED.proposed_title,
                            language = EXCLUDED.language,
                            periodicity = EXCLUDED.periodicity,
                            status = 'PENDING'
                        """,
                        (
                            application_number,
                            title,
                            language,
                            periodicity,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO public.applications
                        (
                            proposed_title,
                            language,
                            periodicity,
                            status
                        )
                        VALUES (%s, %s, %s, 'PENDING')
                        """,
                        (
                            title,
                            language,
                            periodicity,
                        ),
                    )

    def candidates(
        self,
        title: str,
        application_number: str | None = None,
        limit: int = 100,
    ) -> list[TitleRecord]:
        """Return registered titles and OTHER pending applications."""

        if not DATABASE_URL:
            return []

        embedding = self.model.encode(title).tolist()

        records: list[TitleRecord] = []
        seen: set[tuple[str, str, str]] = set()

        with psycopg.connect(DATABASE_URL) as conn:
            register_vector(conn)

            with conn.cursor() as cur:
                # Registered publications
                cur.execute(
                    """
                    SELECT
                        title,
                        language,
                        periodicity
                    FROM public.prgi_titles
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (str(embedding), limit),
                )

                for row in cur.fetchall():
                    key = (
                        row[0].strip().lower(),
                        row[1],
                        row[2],
                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    records.append(
                        TitleRecord(
                            title=row[0],
                            language=row[1],
                            periodicity=row[2],
                            source="REGISTERED",
                        )
                    )

                # Pending applications.
                # Exclude ONLY the current application when an identity
                # was supplied.
                if application_number:
                    cur.execute(
                        """
                        SELECT
                            proposed_title,
                            language,
                            periodicity
                        FROM public.applications
                        WHERE status = 'PENDING'
                          AND (
                              application_number IS NULL
                              OR application_number <> %s
                          )
                        LIMIT %s
                        """,
                        (
                            application_number,
                            limit,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            proposed_title,
                            language,
                            periodicity
                        FROM public.applications
                        WHERE status = 'PENDING'
                        LIMIT %s
                        """,
                        (limit,),
                    )

                for row in cur.fetchall():
                    key = (
                        row[0].strip().lower(),
                        row[1],
                        row[2],
                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    records.append(
                        TitleRecord(
                            title=row[0],
                            language=row[1],
                            periodicity=row[2],
                            source="PENDING_APPLICATION",
                        )
                    )

        return records


title_store = TitleStore()