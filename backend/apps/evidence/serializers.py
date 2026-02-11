from rest_framework import serializers
from .models import EvidenceItem, EvidenceFile, ControlEvidenceLink


class EvidenceFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceFile
        fields = [
            'id',
            'filename',
            'content_type',
            'size_bytes',
            'sha256',
            'uploaded_at',
        ]


class EvidenceItemSerializer(serializers.ModelSerializer):
    files = EvidenceFileSerializer(many=True, read_only=True)

    class Meta:
        model = EvidenceItem
        fields = [
            'id',
            'title',
            'category',
            'subtype',
            'notes',
            'event_date',
            'valid_from',
            'valid_until',
            'created_by',
            'created_at',
            'files',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'files']


class ControlEvidenceLinkSerializer(serializers.ModelSerializer):
    evidence_item = EvidenceItemSerializer(read_only=True)

    class Meta:
        model = ControlEvidenceLink
        fields = [
            'id',
            'control',
            'evidence_item',
            'relevance_note',
            'linked_by',
            'linked_at',
        ]
        read_only_fields = ['id', 'control', 'linked_by', 'linked_at', 'evidence_item']
