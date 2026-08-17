import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

# Load environment variables from backend or ai-service .env
env_path = Path(__file__).resolve().parents[1] / "ai-service" / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "sample_titles.json"
SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

def seed_database():
    print("Loading model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Connecting to database...")
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    
    with conn.cursor() as cur:
        # 1. Apply schema
        print("Applying schema...")
        with open(SCHEMA_FILE, "r") as f:
            schema_sql = f.read()
        cur.execute(schema_sql)

        # Register vector type
        register_vector(conn)

        # 2. Check if data exists
        cur.execute("SELECT COUNT(*) FROM public.prgi_titles")
        count = cur.fetchone()[0]
        if count > 0:
            print(f"Database already has {count} records. Truncating for seed...")
            cur.execute("TRUNCATE TABLE public.prgi_titles RESTART IDENTITY")

        # 3. Read data
        print("Reading sample data...")
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            rows = json.load(f)

        # 4. Process and insert
        print(f"Inserting {len(rows)} records...")
        
        for row in rows:
            title = row["title"]
            language = row["language"]
            periodicity = row["periodicity"]
            
            # Generate embedding
            embedding = model.encode(title).tolist()
            
            cur.execute(
                """
                INSERT INTO public.prgi_titles 
                (title, language, periodicity, publication_state, publication_district, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (title, language, periodicity, "Unknown", "Unknown", embedding)
            )

    conn.close()
    print("Seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
