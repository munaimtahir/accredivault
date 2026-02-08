from rest_framework import serializers
from .models import Control, StandardPack


class ControlSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Control
        fields = ['id', 'control_code', 'section', 'indicator', 'sort_order', 'active', 'status']
    
    def get_status(self, obj):
        # Hardcoded for MVP (Prompt 0)
        return 'NOT_STARTED'


class StandardPackSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardPack
        fields = ['id', 'authority_code', 'name', 'version', 'status', 'published_at', 'created_at']
