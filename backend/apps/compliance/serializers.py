from rest_framework import serializers

from apps.compliance.models import ControlStatusCache, ControlVerification, ExportJob


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
