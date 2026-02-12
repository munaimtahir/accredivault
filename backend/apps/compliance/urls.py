from django.urls import path

from apps.compliance.views import (
    ControlExportView,
    ControlRejectView,
    ControlStatusView,
    ControlVerifyView,
    ExportDownloadView,
)

urlpatterns = [
    path('controls/<int:control_id>/status', ControlStatusView.as_view(), name='control-status'),
    path('controls/<int:control_id>/verify', ControlVerifyView.as_view(), name='control-verify'),
    path('controls/<int:control_id>/reject', ControlRejectView.as_view(), name='control-reject'),
    path('exports/control/<int:control_id>', ControlExportView.as_view(), name='control-export'),
    path('exports/<uuid:job_id>/download', ExportDownloadView.as_view(), name='export-download'),
]
