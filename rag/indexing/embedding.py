import os
import time
from typing import List

EMBEDDING_MODEL = "models/text-embedding-004"
MAX_RETRIES = 2
BACKOFF_BASE_SECONDS = 5


def _configure():
    import google.generativeai as genai

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY tidak tersedia")
    genai.configure(api_key=api_key)
    return genai


def embed_text(text: str) -> List[float]:
    genai = _configure()
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            result = genai.embed_content(model=EMBEDDING_MODEL, content=text, task_type="retrieval_document")
            return result["embedding"]
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
    raise RuntimeError(f"Gagal embed chunk setelah {MAX_RETRIES} retry") from last_error


def embed_batch(texts: List[str]) -> List[List[float]]:
    return [embed_text(text) for text in texts]
