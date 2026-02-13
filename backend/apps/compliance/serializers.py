from rest_framework import serializers

from apps.compliance.models import ComplianceAlert, ControlNote, ControlStatusCache, ControlVerification, ExportJob


class ControlStatusCacheSerializer(serializers.ModelSerializer):
    control_id = serializers.IntegerField(source='control.id', read_only=True)

    class Meta:
        model = ControlStatusCache
        fields = [
            'control_id',
            'computed_status',
            'last_evidence_date',
            'next_due_date',
            'computed_at',
            'details_json',
        ]


class ControlVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlVerification
        fields = [
            'id',
            'control',
            'status',
            'remarks',
            'verified_by',
            'verified_at',
            'evidence_snapshot_at',
        ]


class ExportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportJob
        fields = [
            'id',
            'job_type',
            'status',
            'standard_pack',
            'control',
            'section_code',
            'filters_json',
            'created_by',
            'created_at',
            'completed_at',
            'bucket',
            'object_key',
            'filename',
            'size_bytes',
            'sha256',
            'error_text',
        ]


class ControlNoteSerializer(serializers.ModelSerializer):
    control = serializers.IntegerField(source='control.id', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)

    class Meta:
        model = ControlNote
        fields = [
            'id',
            'control',
            'note_type',
            'text',
            'created_by',
            'created_by_username',
            'created_at',
            'resolved',
            'resolved_at',
            'resolved_by',
            'resolved_by_username',
        ]
        read_only_fields = ['id', 'control', 'created_by', 'created_at', 'resolved_at', 'resolved_by']


class ComplianceAlertSerializer(serializers.ModelSerializer):
    control_id = serializers.IntegerField(source='control.id', read_only=True)
    control_code = serializers.CharField(source='control.control_code', read_only=True)

    class Meta:
        model = ComplianceAlert
        fields = [
            'id',
            'control_id',
            'control_code',
            'alert_type',
            'triggered_at',
            'cleared_at',
        ]
