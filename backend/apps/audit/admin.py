from django.contrib import admin
from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'actor', 'action', 'entity_type', 'entity_id']
    list_filter = ['action', 'entity_type', 'created_at']
    search_fields = ['entity_id', 'actor__username']
    readonly_fields = ['actor', 'action', 'entity_type', 'entity_id', 'before_json', 'after_json', 'created_at', 'ip_address', 'user_agent']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
