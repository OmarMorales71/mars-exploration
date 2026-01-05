import os

def get_embedder() -> dict:
    return {
        "provider": os.getenv("EMBEDDINGS_PROVIDER", "ollama"),
        "config": {
            "model": os.getenv(
                "EMBEDDINGS_MODEL",
                "nomic-embed-text:latest"
            )
        }
    }