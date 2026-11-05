
import requests

response = requests.post(
    "http://localhost:8000/chat/stream",
    json={"message": "Explain RAG in simple words."},
    stream=True,
)

print("Status:", response.status_code)
response.raise_for_status()

print("\nStreaming response:\n")

for chunk in response.iter_content(chunk_size=None):
    if chunk:
        print(chunk.decode(), end="", flush=True)

print("\n\nUsage:")

usage = requests.get("http://localhost:8000/usage")
print(usage.json())
