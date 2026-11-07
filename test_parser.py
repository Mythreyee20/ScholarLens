
from app.services.pdf_parser import extract_folder, chunk_pages

PDF_FOLDER = "data/raw/nsp_guidelines"

print("Reading PDF files...")
pages = extract_folder(PDF_FOLDER)

print("\nCreating text chunks...")
chunks = chunk_pages(
    pages,
    chunk_size=1000,
    overlap=150,
)

print("\n========== CHUNKING SUMMARY ==========")
print("Total pages extracted:", len(pages))
print("Total chunks created:", len(chunks))

if chunks:
    print("\nFirst chunk preview:")
    print("Document:", chunks[0]["document"])
    print("Page:", chunks[0]["page"])
    print("Headings:", chunks[0]["headings"])
    print("Text:", chunks[0]["chunk_text"][:500])

    print("\nLast chunk preview:")
    print("Document:", chunks[-1]["document"])
    print("Page:", chunks[-1]["page"])
    print("Text:", chunks[-1]["chunk_text"][:200])
