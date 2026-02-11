from typing import Optional
from apps.audit.models import AuditEvent


def _get_client_ip(request) -> Optional[str]:
    if request is None:
        return None
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    real_ip = request.META.get('HTTP_X_REAL_IP')
    if real_ip:
        return real_ip.strip()
    return request.META.get('REMOTE_ADDR')


def create_audit_event(*, request, action, entity_type, entity_id, before_json=None, after_json=None):
    actor = None
    if request is not None and getattr(request, 'user', None) is not None:
        if request.user.is_authenticated:
            actor = request.user

    AuditEvent.objects.create(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        before_json=before_json,
        after_json=after_json,
        ip_address=_get_client_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT', '') if request is not None else ''),
    )
