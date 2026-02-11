from django.urls import path
from .views import (
    EvidenceItemCreateView,
    EvidenceFileUploadView,
    EvidenceFileDownloadView,
    ControlEvidenceLinkView,
    ControlEvidenceUnlinkView,
    ControlTimelineView,
)

urlpatterns = [
    path('evidence-items', EvidenceItemCreateView.as_view(), name='evidence-item-create'),
    path('evidence-items/<uuid:evidence_item_id>/files', EvidenceFileUploadView.as_view(), name='evidence-item-upload'),
    path('evidence-files/<int:file_id>/download', EvidenceFileDownloadView.as_view(), name='evidence-file-download'),
    path('controls/<int:control_id>/link-evidence', ControlEvidenceLinkView.as_view(), name='control-link-evidence'),
    path('controls/<int:control_id>/unlink-evidence/<int:link_id>', ControlEvidenceUnlinkView.as_view(), name='control-unlink-evidence'),
    path('controls/<int:control_id>/timeline', ControlTimelineView.as_view(), name='control-timeline'),
]
