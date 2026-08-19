import re

from django.db import transaction

from .embeddings import embed_texts
from .models import KnowledgeChunk


CHUNK_SIZE = 1400
CHUNK_OVERLAP = 180


def split_text(text):
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not cleaned:
        return []
    chunks = []
    cursor = 0
    while cursor < len(cleaned):
        end = min(len(cleaned), cursor + CHUNK_SIZE)
        if end < len(cleaned):
            boundary = max(cleaned.rfind("\n\n", cursor, end), cleaned.rfind(". ", cursor, end))
            if boundary > cursor + CHUNK_SIZE // 2:
                end = boundary + 1
        chunks.append(cleaned[cursor:end].strip())
        if end >= len(cleaned):
            break
        cursor = max(cursor + 1, end - CHUNK_OVERLAP)
    return [chunk for chunk in chunks if chunk]


@transaction.atomic
def index_note(note):
    note.chunks.all().delete()
    values = split_text(f"{note.title}\n\n{note.content}")
    embeddings = embed_texts(values)
    KnowledgeChunk.objects.bulk_create(
        [
            KnowledgeChunk(
                owner=note.owner,
                note=note,
                source_type=KnowledgeChunk.Source.NOTE,
                chunk_index=index,
                content=content,
                embedding=embeddings[index],
                metadata={"title": note.title, "context": note.context_label},
            )
            for index, content in enumerate(values)
        ]
    )


@transaction.atomic
def index_document(document):
    document.chunks.all().delete()
    values = split_text(f"{document.title}\n\n{document.extracted_text}")
    embeddings = embed_texts(values)
    KnowledgeChunk.objects.bulk_create(
        [
            KnowledgeChunk(
                owner=document.owner,
                document=document,
                source_type=KnowledgeChunk.Source.DOCUMENT,
                chunk_index=index,
                content=content,
                embedding=embeddings[index],
                metadata={"title": document.title, "filename": document.original_filename},
            )
            for index, content in enumerate(values)
        ]
    )
