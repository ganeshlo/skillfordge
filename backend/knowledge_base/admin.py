from django.contrib import admin

from .models import (
    CodeSnippet,
    DocumentHighlight,
    KnowledgeAIInteraction,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeFolder,
    KnowledgeNote,
    KnowledgeNoteVersion,
    KnowledgeTag,
)

admin.site.register(
    [
        KnowledgeFolder,
        KnowledgeTag,
        KnowledgeNote,
        KnowledgeNoteVersion,
        KnowledgeDocument,
        DocumentHighlight,
        CodeSnippet,
        KnowledgeChunk,
        KnowledgeAIInteraction,
    ]
)
