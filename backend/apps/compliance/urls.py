from django.urls import path

from apps.compliance.views import (
    AlertsListView,
    ControlNoteDetailView,
    ControlNotesView,
    ControlExportView,
    ControlRejectView,
    ControlStatusView,
    ControlVerifyView,
    DashboardSummaryView,
    ExportDownloadView,
    FullPackExportView,
    SectionExportView,
)

urlpatterns = [
    path('controls/<int:control_id>/status', ControlStatusView.as_view(), name='control-status'),
    path('controls/<int:control_id>/verify', ControlVerifyView.as_view(), name='control-verify'),
    path('controls/<int:control_id>/reject', ControlRejectView.as_view(), name='control-reject'),
    path('controls/<int:control_id>/notes', ControlNotesView.as_view(), name='control-notes'),
    path('controls/<int:control_id>/notes/<uuid:note_id>', ControlNoteDetailView.as_view(), name='control-note-detail'),
    path('dashboard/summary', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('alerts', AlertsListView.as_view(), name='alerts-list'),
    path('exports/control/<int:control_id>', ControlExportView.as_view(), name='control-export'),
    path('exports/section/<str:section_code>', SectionExportView.as_view(), name='section-export'),
    path('exports/full', FullPackExportView.as_view(), name='full-export'),
    path('exports/<uuid:job_id>/download', ExportDownloadView.as_view(), name='export-download'),
]
