import os
import hashlib

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

from app.services.pdf_parser import extract_folder, chunk_pages


PDF_FOLDER = "data/raw/nsp_guidelines"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 32


def main():
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL missing in .env file")

    print("1. Loading PDF files...")
    pages = extract_folder(PDF_FOLDER)

    print("\n2. Creating chunks...")
    chunks = chunk_pages(pages, chunk_size=1000, overlap=150)
    print(f"Total chunks: {len(chunks)}")

    print("\n3. Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("\n4. Connecting to PostgreSQL...")
    with psycopg.connect(database_url) as conn:
        register_vector(conn)

        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE scholarship_chunks
                ADD COLUMN IF NOT EXISTS content_hash TEXT;
            """)
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_scholarship_chunks_hash
                ON scholarship_chunks (content_hash);
            """)
        conn.commit()

        print("\n5. Generating embeddings and saving in batches...")

        saved = 0

        for start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[start:start + BATCH_SIZE]
            texts = [item["chunk_text"] for item in batch]

            embeddings = model.encode(
                texts,
                batch_size=8,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            rows = []

            for item, embedding in zip(batch, embeddings):
                unique_text = (
                    f'{item["document"]}|{item["page"]}|'
                    f'{item["chunk_text"]}'
                )
                content_hash = hashlib.sha256(
                    unique_text.encode("utf-8")
                ).hexdigest()

                rows.append((
                    item["document"],
                    item["page"],
                    item["headings"],
                    item["chunk_text"],
                    embedding.tolist(),
                    content_hash,
                ))

            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO scholarship_chunks
                    (document, page, headings, chunk_text, embedding, content_hash)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (content_hash) DO NOTHING;
                """, rows)

            conn.commit()
            saved += len(batch)

            print(f"Processed {saved}/{len(chunks)} chunks")

    print("\nEmbedding process completed!")


if __name__ == "__main__":
    main()