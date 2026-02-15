from django.urls import path
from .views import AuditEventsListView

urlpatterns = [
    path('audit/events', AuditEventsListView.as_view(), name='audit-events-list'),
]
