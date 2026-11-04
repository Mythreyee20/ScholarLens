import requests

response = requests.post(
    "http://localhost:8000/chat/stream",
    json={"message": "Explain RAG in simple words."},
    stream=True,
)

for chunk in response.iter_content(chunk_size=None):
    if chunk:
        print(chunk.decode(), end="", flush=True)