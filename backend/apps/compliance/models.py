import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.standards.models import Control, StandardPack


class EvidenceRule(models.Model):
    SCOPE_CONTROL = 'CONTROL'
    SCOPE_SECTION = 'SECTION'
    SCOPE_TYPE_CHOICES = [
        (SCOPE_CONTROL, 'Control'),
        (SCOPE_SECTION, 'Section'),
    ]

    RULE_ONE_TIME = 'ONE_TIME'
    RULE_FREQUENCY = 'FREQUENCY'
    RULE_ROLLING_WINDOW = 'ROLLING_WINDOW'
    RULE_EXPIRY = 'EXPIRY'
    RULE_COUNT_IN_WINDOW = 'COUNT_IN_WINDOW'
    RULE_TYPE_CHOICES = [
        (RULE_ONE_TIME, 'One Time'),
        (RULE_FREQUENCY, 'Frequency'),
        (RULE_ROLLING_WINDOW, 'Rolling Window'),
        (RULE_EXPIRY, 'Expiry'),
        (RULE_COUNT_IN_WINDOW, 'Count In Window'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    standard_pack = models.ForeignKey(StandardPack, on_delete=models.CASCADE, related_name='evidence_rules', db_index=True)
    scope_type = models.CharField(max_length=20, choices=SCOPE_TYPE_CHOICES, db_index=True)
    control = models.ForeignKey(
        Control,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='rules',
    )
    section_code = models.CharField(max_length=10, null=True, blank=True, db_index=True)

    rule_type = models.CharField(max_length=30, choices=RULE_TYPE_CHOICES)
    window_days = models.IntegerField(null=True, blank=True)
    frequency_days = models.IntegerField(null=True, blank=True)
    min_items = models.IntegerField(default=1)
    requires_verification = models.BooleanField(default=False)
    acceptable_categories = models.JSONField(default=list, blank=True)
    acceptable_subtypes = models.JSONField(default=list, blank=True)
    enabled = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.standard_pack.version}:{self.scope_type}:{self.rule_type}"

    def clean(self):
        errors = {}

        if self.scope_type == self.SCOPE_CONTROL:
            if self.control is None:
                errors['control'] = 'control must be set when scope_type=CONTROL'
            if self.section_code:
                errors['section_code'] = 'section_code must be empty when scope_type=CONTROL'
        elif self.scope_type == self.SCOPE_SECTION:
            if not self.section_code:
                errors['section_code'] = 'section_code must be set when scope_type=SECTION'
            if self.control is not None:
                errors['control'] = 'control must be empty when scope_type=SECTION'

        if self.min_items is None or self.min_items <= 0:
            errors['min_items'] = 'min_items must be > 0'

        if self.rule_type == self.RULE_FREQUENCY:
            if not self.frequency_days or self.frequency_days <= 0:
                errors['frequency_days'] = 'frequency_days is required and must be > 0 for FREQUENCY'
        elif self.rule_type == self.RULE_ROLLING_WINDOW:
            if not self.window_days or self.window_days <= 0:
                errors['window_days'] = 'window_days is required and must be > 0 for ROLLING_WINDOW'
        elif self.rule_type == self.RULE_COUNT_IN_WINDOW:
            if not self.window_days or self.window_days <= 0:
                errors['window_days'] = 'window_days is required and must be > 0 for COUNT_IN_WINDOW'
            if not self.min_items or self.min_items <= 0:
                errors['min_items'] = 'min_items is required and must be > 0 for COUNT_IN_WINDOW'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ControlStatusCache(models.Model):
    control = models.OneToOneField(Control, on_delete=models.CASCADE, related_name='status_cache')
    computed_status = models.CharField(max_length=20, db_index=True)
    last_evidence_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    computed_at = models.DateTimeField(auto_now=True)
    details_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-computed_at']

    def __str__(self):
        return f"{self.control_id}:{self.computed_status}"


class ControlVerification(models.Model):
    STATUS_VERIFIED = 'VERIFIED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name='verifications', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    remarks = models.TextField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    verified_at = models.DateTimeField(auto_now_add=True)
    evidence_snapshot_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-verified_at']

    def __str__(self):
        return f"{self.control_id}:{self.status}:{self.verified_at.isoformat()}"


class ExportJob(models.Model):
    JOB_CONTROL_PDF = 'CONTROL_PDF'
    JOB_SECTION_PACK = 'SECTION_PACK'
    JOB_FULL_PACK = 'FULL_PACK'
    JOB_TYPE_CHOICES = [
        (JOB_CONTROL_PDF, 'Control PDF'),
        (JOB_SECTION_PACK, 'Section Pack'),
        (JOB_FULL_PACK, 'Full Pack'),
    ]

    STATUS_QUEUED = 'QUEUED'
    STATUS_RUNNING = 'RUNNING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_type = models.CharField(max_length=30, choices=JOB_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    standard_pack = models.ForeignKey(StandardPack, on_delete=models.CASCADE, related_name='export_jobs', db_index=True)
    control = models.ForeignKey(Control, null=True, blank=True, on_delete=models.CASCADE, related_name='export_jobs', db_index=True)
    section_code = models.CharField(max_length=10, null=True, blank=True, db_index=True)
    filters_json = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    bucket = models.CharField(max_length=255)
    object_key = models.CharField(max_length=1024, unique=True)
    filename = models.CharField(max_length=255)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    error_text = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.job_type}:{self.status}:{self.id}"


class ControlNote(models.Model):
    TYPE_INTERNAL = 'INTERNAL'
    TYPE_INSPECTION = 'INSPECTION'
    TYPE_CORRECTIVE_ACTION = 'CORRECTIVE_ACTION'
    NOTE_TYPE_CHOICES = [
        (TYPE_INTERNAL, 'Internal'),
        (TYPE_INSPECTION, 'Inspection'),
        (TYPE_CORRECTIVE_ACTION, 'Corrective Action'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name='notes', db_index=True)
    note_type = models.CharField(max_length=30, choices=NOTE_TYPE_CHOICES, db_index=True)
    text = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='resolved_control_notes',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.control_id}:{self.note_type}:{self.id}"


class ComplianceAlert(models.Model):
    TYPE_OVERDUE = 'OVERDUE'
    TYPE_NEAR_DUE = 'NEAR_DUE'
    ALERT_TYPE_CHOICES = [
        (TYPE_OVERDUE, 'Overdue'),
        (TYPE_NEAR_DUE, 'Near Due'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name='alerts', db_index=True)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES, db_index=True)
    triggered_at = models.DateTimeField(auto_now_add=True, db_index=True)
    cleared_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-triggered_at']

    def __str__(self):
        return f"{self.control_id}:{self.alert_type}:{'active' if self.cleared_at is None else 'cleared'}"
