import re

from django.db import connection
from django.db.models import Q
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from pgvector.django import CosineDistance

from .embeddings import embed_texts, embedding_available
from .models import CodeSnippet, KnowledgeChunk


def _source_result(chunk, score):
    source = chunk.note or chunk.document
    return {
        "id": str(chunk.id),
        "source_type": chunk.source_type,
        "source_id": str(source.id),
        "title": source.title,
        "excerpt": chunk.content[:420],
        "score": round(float(score), 5),
        "metadata": chunk.metadata,
    }


def search_knowledge(*, user, query, limit=12):
    base = KnowledgeChunk.objects.filter(owner=user).select_related("note", "document")
    ranked = {}
    if connection.vendor == "postgresql":
        search_query = SearchQuery(query, search_type="websearch")
        keyword = (
            base.annotate(
                rank=SearchRank(
                    SearchVector("content", config="english"), search_query
                )
            )
            .filter(rank__gt=0)
            .order_by("-rank")[:limit]
        )
        for chunk in keyword:
            ranked[str(chunk.id)] = (chunk, float(chunk.rank))
    else:
        terms = [
            term for term in re.findall(r"[A-Za-z0-9_+-]{3,}", query)
            if term.lower() not in {"what", "when", "where", "which", "with", "from", "about", "your", "this", "that", "does", "why"}
        ]
        condition = Q()
        for term in terms[:8]:
            condition |= Q(content__icontains=term)
        fallback = base.filter(condition) if condition else base.none()
        for position, chunk in enumerate(fallback[:limit]):
            ranked[str(chunk.id)] = (chunk, 1 / (position + 1))

    mode = "keyword"
    if embedding_available():
        query_embedding = embed_texts([query])[0]
        semantic = (
            base.filter(embedding__isnull=False)
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[:limit]
        )
        for position, chunk in enumerate(semantic):
            semantic_score = max(0.0, 1.0 - float(chunk.distance))
            key = str(chunk.id)
            previous = ranked.get(key)
            ranked[key] = (chunk, semantic_score + (previous[1] if previous else 0))
        mode = "hybrid"

    results = [
        _source_result(chunk, score)
        for chunk, score in sorted(ranked.values(), key=lambda item: item[1], reverse=True)[:limit]
    ]
    snippets = CodeSnippet.objects.filter(
        owner=user, deleted_at__isnull=True, title__icontains=query
    )[: max(0, min(4, limit - len(results)))]
    results.extend(
        {
            "id": str(snippet.id),
            "source_type": "snippet",
            "source_id": str(snippet.id),
            "title": snippet.title,
            "excerpt": snippet.code[:420],
            "score": 0.5,
            "metadata": {"language": snippet.language},
        }
        for snippet in snippets
    )
    return {"mode": mode, "results": results}
