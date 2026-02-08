from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditEvent(models.Model):
    """
    Append-only audit log for tracking all changes in the system.
    """
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, db_index=True, help_text="e.g., CREATE, UPDATE, DELETE")
    entity_type = models.CharField(max_length=50, db_index=True, help_text="e.g., Control, Evidence")
    entity_id = models.CharField(max_length=100, db_index=True, help_text="ID of the entity")
    before_json = models.JSONField(null=True, blank=True, help_text="State before change")
    after_json = models.JSONField(null=True, blank=True, help_text="State after change")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Event'
        verbose_name_plural = 'Audit Events'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['actor', 'created_at']),
        ]
    
    def __str__(self):
        actor_name = self.actor.username if self.actor else 'System'
        return f"{actor_name} {self.action} {self.entity_type} {self.entity_id} at {self.created_at}"
