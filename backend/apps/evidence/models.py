import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.standards.models import Control

User = get_user_model()


class EvidenceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, db_index=True)
    subtype = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    event_date = models.DateField(db_index=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evidence_items',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-event_date', '-created_at']
        indexes = [
            models.Index(fields=['category', 'event_date']),
        ]

    def __str__(self):
        return f"{self.title} ({self.category})"


class EvidenceFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence_item = models.ForeignKey(
        EvidenceItem,
        on_delete=models.CASCADE,
        related_name='files',
    )
    bucket = models.CharField(max_length=255)
    object_key = models.CharField(max_length=1024, unique=True)
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    size_bytes = models.BigIntegerField()
    sha256 = models.CharField(max_length=64, db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.filename} ({self.evidence_item_id})"


class ControlEvidenceLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    control = models.ForeignKey(
        Control,
        on_delete=models.CASCADE,
        related_name='evidence_links',
    )
    evidence_item = models.ForeignKey(
        EvidenceItem,
        on_delete=models.CASCADE,
        related_name='control_links',
    )
    relevance_note = models.TextField(null=True, blank=True)
    linked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evidence_links',
    )
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-linked_at']
        unique_together = [['control', 'evidence_item']]
        indexes = [
            models.Index(fields=['control']),
            models.Index(fields=['evidence_item']),
        ]

    def __str__(self):
        return f"{self.control_id} -> {self.evidence_item_id}"
