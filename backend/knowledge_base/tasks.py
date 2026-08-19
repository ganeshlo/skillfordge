from celery import shared_task

from .extraction import extract_document
from .indexing import index_document, index_note
from .models import KnowledgeDocument, KnowledgeNote


@shared_task(autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def index_note_task(note_id):
    note = KnowledgeNote.objects.filter(id=note_id, deleted_at__isnull=True).first()
    if note:
        index_note(note)


@shared_task(autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def process_document_task(document_id):
    document = KnowledgeDocument.objects.filter(
        id=document_id, deleted_at__isnull=True
    ).first()
    if not document:
        return
    try:
        text, page_count = extract_document(document)
        document.extracted_text = text
        document.page_count = page_count
        document.status = KnowledgeDocument.Status.READY
        document.error_code = ""
        document.save(
            update_fields=[
                "extracted_text", "page_count", "status", "error_code", "updated_at"
            ]
        )
        index_document(document)
    except Exception:
        document.status = KnowledgeDocument.Status.FAILED
        document.error_code = "extraction_failed"
        document.save(update_fields=["status", "error_code", "updated_at"])
        raise
