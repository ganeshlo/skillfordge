from .models import AuditLog


def record_audit_event(*, action, actor=None, organization=None, target=None, request=None, metadata=None):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "") if request else ""
    ip_address = forwarded.split(",")[0].strip() if forwarded else (request.META.get("REMOTE_ADDR") if request else None)
    return AuditLog.objects.create(
        actor=actor,
        organization_id=getattr(organization, "id", None),
        action=action,
        target_type=target._meta.label if target is not None else "",
        target_id=str(target.pk) if target is not None else "",
        request_id=getattr(request, "request_id", ""),
        ip_address=ip_address,
        metadata=metadata or {},
    )

