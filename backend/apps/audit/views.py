from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import CanViewAudit
from .models import AuditEvent


class AuditEventsListView(APIView):
    """GET /api/v1/audit/events - List audit events with filters."""
    permission_classes = [CanViewAudit]

    def get(self, request):
        qs = AuditEvent.objects.select_related('actor').order_by('-created_at')
        action = request.query_params.get('action')
        entity_type = request.query_params.get('entity_type')
        after = request.query_params.get('after')
        before = request.query_params.get('before')
        q = request.query_params.get('q')

        if action:
            qs = qs.filter(action__icontains=action)
        if entity_type:
            qs = qs.filter(entity_type__icontains=entity_type)
        if after:
            qs = qs.filter(created_at__gte=after)
        if before:
            qs = qs.filter(created_at__lte=before)
        if q:
            qs = qs.filter(
                Q(action__icontains=q) |
                Q(entity_type__icontains=q) |
                Q(entity_id__icontains=q)
            )

        # Limit to 200 for performance
        events = list(qs[:200])
        data = [
            {
                'id': e.pk,
                'created_at': e.created_at.isoformat() if e.created_at else None,
                'actor': e.actor.username if e.actor else None,
                'action': e.action,
                'entity_type': e.entity_type,
                'entity_id': e.entity_id[:20] + '...' if len(str(e.entity_id)) > 20 else str(e.entity_id),
                'summary': f"{e.action} {e.entity_type} {e.entity_id}",
            }
            for e in events
        ]
        return Response(data, status=200)
