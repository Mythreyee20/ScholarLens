
import os

from app.services.embed_store import main


# Existing shared NSP document ingestion
def ingest_all_pdfs():
    main()
    return "Shared PDF ingestion completed"


# Client-specific PDF ingestion
def ingest_client_pdfs(pdf_folder: str, client_id: int):
    if not os.path.isdir(pdf_folder):
        raise FileNotFoundError(
            f"Client PDF folder not found: {pdf_folder}"
        )

    main(
        pdf_folder=pdf_folder,
        client_id=client_id,
    )

    return f"PDF ingestion completed for client {client_id}"
