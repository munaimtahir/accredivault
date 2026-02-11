from rest_framework import serializers
from .models import Control, StandardPack


class ControlSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    last_evidence_date = serializers.SerializerMethodField()
    next_due_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Control
        fields = [
            'id',
            'control_code',
            'section',
            'standard',
            'indicator',
            'sort_order',
            'active',
            'status',
            'last_evidence_date',
            'next_due_date',
        ]
    
    def get_status(self, obj):
        cache = getattr(obj, 'status_cache', None)
        if cache:
            return cache.computed_status
        return 'NOT_STARTED'

    def get_last_evidence_date(self, obj):
        cache = getattr(obj, 'status_cache', None)
        if cache and cache.last_evidence_date:
            return cache.last_evidence_date
        return None

    def get_next_due_date(self, obj):
        cache = getattr(obj, 'status_cache', None)
        if cache and cache.next_due_date:
            return cache.next_due_date
        return None


class StandardPackSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardPack
        fields = ['id', 'authority_code', 'name', 'version', 'status', 'published_at', 'created_at']
