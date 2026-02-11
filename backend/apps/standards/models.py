from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import hashlib


class StandardPack(models.Model):
    """
    Represents a version of a standard checklist (e.g., PHC Lab Licensing Checklist v1.0).
    Immutable after publishing.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    authority_code = models.CharField(max_length=50, db_index=True, help_text="e.g., PHC")
    name = models.CharField(max_length=255, help_text="e.g., PHC Lab Licensing Checklist")
    version = models.CharField(max_length=50, help_text="e.g., 1.0")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    checksum = models.CharField(max_length=64, unique=True, help_text="SHA256 of source file")
    published_at = models.DateTimeField(null=True, blank=True)
    source_file_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['authority_code', 'version']]
        ordering = ['-created_at']
        verbose_name = 'Standard Pack'
        verbose_name_plural = 'Standard Packs'
    
    def __str__(self):
        return f"{self.authority_code} {self.name} v{self.version} ({self.status})"
    
    def publish(self):
        """Mark pack as published"""
        if self.status != 'published':
            self.status = 'published'
            self.published_at = timezone.now()
            self.save()
    
    def archive(self):
        """Archive this pack"""
        if self.status == 'published':
            self.status = 'archived'
            self.save()


class Control(models.Model):
    """
    Individual control item from a standard pack.
    Immutable after pack is published.
    """
    standard_pack = models.ForeignKey(
        StandardPack, 
        on_delete=models.CASCADE, 
        related_name='controls'
    )
    control_code = models.CharField(
        max_length=50, 
        db_index=True,
        help_text="e.g., PHC-ROM-001"
    )
    section = models.CharField(max_length=255, db_index=True, help_text="Section name")
    standard = models.TextField(help_text="Standard description")
    indicator = models.TextField(help_text="Indicator/requirement text")
    sort_order = models.IntegerField(default=0, db_index=True, help_text="Global sort order")
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Control'
        verbose_name_plural = 'Controls'
        unique_together = [['standard_pack', 'control_code']]
    
    def __str__(self):
        return f"{self.control_code}: {self.section}"
    
    def clean(self):
        """Enforce immutability after pack is published"""
        if self.pk:  # Only check on update, not create
            if self.standard_pack.status == 'published':
                # Get original values
                original = Control.objects.get(pk=self.pk)
                immutable_fields = ['section', 'standard', 'indicator', 'control_code', 'sort_order']
                
                for field in immutable_fields:
                    if getattr(self, field) != getattr(original, field):
                        raise ValidationError(
                            f"Cannot modify {field} after standard pack is published"
                        )
    
    def save(self, *args, **kwargs):
        """Enforce immutability on save"""
        self.full_clean()
        super().save(*args, **kwargs)
