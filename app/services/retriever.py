import os
from functools import lru_cache

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    print("Loading embedding model...")
    return SentenceTransformer(MODEL_NAME)


class RetrieverService:

    def retrieve(self, question: str, limit: int = 5) -> list[dict]:
        load_dotenv()

        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            raise RuntimeError("DATABASE_URL is missing.")

        model = get_embedding_model()

        query_embedding = model.encode(
            question,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).tolist()

        try:
            with psycopg.connect(database_url) as conn:
                register_vector(conn)

                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            document,
                            page,
                            headings,
                            chunk_text
                        FROM scholarship_chunks
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> (%s)::vector
                        LIMIT %s;
                        """,
                        (str(query_embedding), limit),
                    )

                    rows = cur.fetchall()

            return [
                {
                    "document": document,
                    "page": page,
                    "headings": headings or [],
                    "chunk_text": chunk_text,
                }
                for document, page, headings, chunk_text in rows
            ]

        except Exception as error:
            raise RuntimeError(
                f"Document retrieval failed: {error}"
            ) from error