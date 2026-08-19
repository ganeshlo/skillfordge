from django.conf import settings
from openai import OpenAI


EMBEDDING_DIMENSIONS = 1536


def embedding_available():
    return bool(settings.OPENAI_API_KEY)


def embed_texts(texts):
    if not texts:
        return []
    if not embedding_available():
        return [None] * len(texts)
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=45, max_retries=2)
    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    ordered = sorted(response.data, key=lambda item: item.index)
    return [item.embedding for item in ordered]
