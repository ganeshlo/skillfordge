import hashlib

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from audit.services import record_audit_event

from .models import (
    CodeSnippet,
    KnowledgeDocument,
    KnowledgeFolder,
    KnowledgeNote,
    KnowledgeNoteVersion,
    KnowledgeTag,
)
from .tasks import index_note_task, process_document_task
from .validation import validate_folder_parent, validate_knowledge_upload

UNSET = object()


def folder_for(user, folder_id):
    if not folder_id:
        return None
    folder = KnowledgeFolder.objects.filter(owner=user, id=folder_id).first()
    if not folder:
        raise ValidationError({"folder_id": "Folder does not belong to your knowledge base."})
    return folder


def tags_for(user, tag_ids):
    if not tag_ids:
        return []
    tags = list(KnowledgeTag.objects.filter(owner=user, id__in=tag_ids))
    if len(tags) != len(set(tag_ids)):
        raise ValidationError({"tag_ids": "One or more tags do not belong to your knowledge base."})
    return tags


@transaction.atomic
def create_folder(*, user, name, parent_id=None, color="#4F46E5", request=None):
    parent = folder_for(user, parent_id)
    validate_folder_parent(owner=user, parent=parent)
    if KnowledgeFolder.objects.filter(owner=user, parent=parent, name__iexact=name.strip()).exists():
        raise ValidationError({"name": "A folder with this name already exists here."})
    folder = KnowledgeFolder.objects.create(
        owner=user, parent=parent, name=name.strip(), color=color
    )
    record_audit_event(action="knowledge.folder_created", actor=user, target=folder, request=request)
    return folder


@transaction.atomic
def create_note(*, user, title, content="", folder_id=None, tag_ids=None, request=None, **values):
    note = KnowledgeNote.objects.create(
        owner=user, folder=folder_for(user, folder_id), title=title.strip(), content=content, **values
    )
    note.tags.set(tags_for(user, tag_ids or []))
    KnowledgeNoteVersion.objects.create(
        note=note, version=1, title=note.title, content=note.content, created_by=user
    )
    transaction.on_commit(lambda: index_note_task.delay(str(note.id)))
    record_audit_event(action="knowledge.note_created", actor=user, target=note, request=request)
    return note


@transaction.atomic
def update_note(*, user, note, folder_id=UNSET, tag_ids=UNSET, request=None, **values):
    changed_content = (
        ("title" in values and values["title"] != note.title)
        or ("content" in values and values["content"] != note.content)
    )
    if folder_id is not UNSET:
        note.folder = folder_for(user, folder_id)
    for field, value in values.items():
        setattr(note, field, value.strip() if field == "title" else value)
    if changed_content:
        note.current_version += 1
    note.save()
    if tag_ids is not UNSET:
        note.tags.set(tags_for(user, tag_ids))
    if changed_content:
        KnowledgeNoteVersion.objects.create(
            note=note,
            version=note.current_version,
            title=note.title,
            content=note.content,
            created_by=user,
        )
        transaction.on_commit(lambda: index_note_task.delay(str(note.id)))
    return note


@transaction.atomic
def create_document(*, user, upload, title="", folder_id=None, tag_ids=None, request=None):
    mime_type = validate_knowledge_upload(upload)
    digest = hashlib.sha256()
    for chunk in upload.chunks():
        digest.update(chunk)
    upload.seek(0)
    document = KnowledgeDocument.objects.create(
        owner=user,
        folder=folder_for(user, folder_id),
        title=title.strip() or upload.name.rsplit(".", 1)[0],
        file=upload,
        original_filename=upload.name[:255],
        mime_type=mime_type,
        size_bytes=upload.size,
        checksum=digest.hexdigest(),
    )
    document.tags.set(tags_for(user, tag_ids or []))
    transaction.on_commit(lambda: process_document_task.delay(str(document.id)))
    record_audit_event(
        action="knowledge.document_uploaded",
        actor=user,
        target=document,
        request=request,
        metadata={"mime_type": mime_type, "size_bytes": upload.size},
    )
    return document


def soft_delete(item, *, user, request=None):
    item.deleted_at = timezone.now()
    item.save(update_fields=["deleted_at", "updated_at"])
    record_audit_event(action="knowledge.item_deleted", actor=user, target=item, request=request)


def owned_or_404(model, *, user, item_id):
    query = {"owner": user, "id": item_id}
    if issubclass(model, (KnowledgeNote, KnowledgeDocument, CodeSnippet)):
        query["deleted_at__isnull"] = True
    item = model.objects.filter(**query).first()
    if not item:
        raise NotFound("Knowledge item not found.")
    return item
