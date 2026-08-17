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
        if not DATABASE_URL:
            return
        
        embedding = self.model.encode(title).tolist()
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.prgi_titles 
                    (title, language, periodicity, source, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector)
                    """,
                    (title, language, periodicity, "PENDING_APPLICATION", str(embedding))
                )

    def candidates(self, title: str, limit: int = 100) -> list[TitleRecord]:
        if not DATABASE_URL:
            return []

        embedding = self.model.encode(title).tolist()
        records = []
        with psycopg.connect(DATABASE_URL) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT title, language, periodicity, COALESCE(source, 'REGISTERED') as source
                    FROM public.prgi_titles
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (str(embedding), limit)
                )
                for row in cur.fetchall():
                    records.append(TitleRecord(title=row[0], language=row[1], periodicity=row[2], source=row[3]))
        return records


title_store = TitleStore()
