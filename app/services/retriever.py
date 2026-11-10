
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

    def retrieve(
        self,
        question: str,
        limit: int = 5,
        client_id: int = None,
    ) -> list[dict]:

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
                        WITH vector_results AS (
                            SELECT
                                id,
                                ROW_NUMBER() OVER (
                                    ORDER BY embedding <=> (%s)::vector
                                ) AS rank
                            FROM scholarship_chunks
                            WHERE embedding IS NOT NULL
                            AND (client_id IS NULL OR client_id = %s)
                            LIMIT 30
                        ),
                        keyword_results AS (
                            SELECT
                                id,
                                ROW_NUMBER() OVER (
                                    ORDER BY ts_rank_cd(
                                        to_tsvector(
                                            'english',
                                            coalesce(document, '') || ' ' ||
                                            coalesce(array_to_string(headings, ' '), '') || ' ' ||
                                            coalesce(chunk_text, '')
                                        ),
                                        websearch_to_tsquery('english', %s)
                                    ) DESC
                                ) AS rank
                            FROM scholarship_chunks
                            WHERE (client_id IS NULL OR client_id = %s)
                            AND to_tsvector(
                                'english',
                                coalesce(document, '') || ' ' ||
                                coalesce(array_to_string(headings, ' '), '') || ' ' ||
                                coalesce(chunk_text, '')
                            ) @@ websearch_to_tsquery('english', %s)
                            LIMIT 30
                        ),
                        combined_results AS (
                            SELECT
                                id,
                                SUM(score) AS combined_score
                            FROM (
                                SELECT
                                    id,
                                    1.0 / (60 + rank) AS score
                                FROM vector_results

                                UNION ALL

                                SELECT
                                    id,
                                    1.0 / (60 + rank) AS score
                                FROM keyword_results
                            ) results
                            GROUP BY id
                        )
                        SELECT
                            s.document,
                            s.page,
                            s.headings,
                            s.chunk_text
                        FROM combined_results c
                        JOIN scholarship_chunks s ON s.id = c.id
                        ORDER BY c.combined_score DESC
                        LIMIT %s;
                        """,
                        (
                            str(query_embedding),
                            client_id,
                            question,
                            client_id,
                            question,
                            limit,
                        ),
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
                f"Hybrid document retrieval failed: {error}"
            ) from error
