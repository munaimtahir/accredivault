from django.contrib import admin

from apps.compliance.models import ControlStatusCache, ControlVerification, EvidenceRule, ExportJob


@admin.register(EvidenceRule)
class EvidenceRuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'standard_pack', 'scope_type', 'control', 'section_code', 'rule_type', 'enabled', 'requires_verification')
    list_filter = ('scope_type', 'rule_type', 'enabled', 'requires_verification', 'standard_pack')
    search_fields = ('section_code', 'control__control_code', 'standard_pack__version')


@admin.register(ControlStatusCache)
class ControlStatusCacheAdmin(admin.ModelAdmin):
    list_display = ('control', 'computed_status', 'last_evidence_date', 'next_due_date', 'computed_at')
    list_filter = ('computed_status',)
    search_fields = ('control__control_code',)


@admin.register(ControlVerification)
class ControlVerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'control', 'status', 'verified_by', 'verified_at', 'evidence_snapshot_at')
    list_filter = ('status', 'verified_at')
    search_fields = ('control__control_code', 'verified_by__username')


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'job_type', 'status', 'standard_pack', 'control', 'created_at', 'completed_at')
    list_filter = ('job_type', 'status', 'standard_pack')
    search_fields = ('object_key', 'filename', 'control__control_code', 'standard_pack__version')
