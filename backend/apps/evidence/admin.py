from django.contrib import admin
from .models import EvidenceItem, EvidenceFile, ControlEvidenceLink


@admin.register(EvidenceItem)
class EvidenceItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'event_date', 'created_at']
    list_filter = ['category']
    search_fields = ['title', 'category', 'notes']
    readonly_fields = ['created_at']


@admin.register(EvidenceFile)
class EvidenceFileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'evidence_item', 'size_bytes', 'uploaded_at']
    search_fields = ['filename', 'sha256']
    readonly_fields = ['uploaded_at']


@admin.register(ControlEvidenceLink)
class ControlEvidenceLinkAdmin(admin.ModelAdmin):
    list_display = ['control', 'evidence_item', 'linked_at']
    search_fields = ['control__control_code', 'evidence_item__title']
    readonly_fields = ['linked_at']
