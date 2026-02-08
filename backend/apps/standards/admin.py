from django.contrib import admin
from .models import StandardPack, Control


@admin.register(StandardPack)
class StandardPackAdmin(admin.ModelAdmin):
    list_display = ['authority_code', 'name', 'version', 'status', 'published_at', 'created_at']
    list_filter = ['status', 'authority_code']
    search_fields = ['name', 'authority_code', 'version']
    readonly_fields = ['checksum', 'created_at', 'updated_at', 'published_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('authority_code', 'name', 'version', 'status')
        }),
        ('Source Information', {
            'fields': ('source_file_name', 'checksum')
        }),
        ('Timestamps', {
            'fields': ('published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of published packs"""
        if obj and obj.status == 'published':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Control)
class ControlAdmin(admin.ModelAdmin):
    list_display = ['control_code', 'section', 'sort_order', 'active', 'standard_pack']
    list_filter = ['section', 'active', 'standard_pack__version', 'standard_pack__authority_code']
    search_fields = ['control_code', 'section', 'standard', 'indicator']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Identification', {
            'fields': ('control_code', 'standard_pack', 'section', 'sort_order', 'active')
        }),
        ('Content', {
            'fields': ('standard', 'indicator')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly if pack is published"""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.standard_pack.status == 'published':
            readonly.extend(['control_code', 'section', 'standard', 'indicator', 'sort_order'])
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion if pack is published"""
        if obj and obj.standard_pack.status == 'published':
            return False
        return super().has_delete_permission(request, obj)
