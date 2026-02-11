# Generated manually for Evidence MVP
from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('standards', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EvidenceItem',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('category', models.CharField(max_length=50, db_index=True)),
                ('subtype', models.CharField(blank=True, max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('event_date', models.DateField(db_index=True)),
                ('valid_from', models.DateField(blank=True, null=True)),
                ('valid_until', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evidence_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-event_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='EvidenceFile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('bucket', models.CharField(max_length=255)),
                ('object_key', models.CharField(max_length=1024, unique=True)),
                ('filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(max_length=255)),
                ('size_bytes', models.BigIntegerField()),
                ('sha256', models.CharField(db_index=True, max_length=64)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('evidence_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='evidence.evidenceitem')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='ControlEvidenceLink',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('relevance_note', models.TextField(blank=True, null=True)),
                ('linked_at', models.DateTimeField(auto_now_add=True)),
                ('control', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidence_links', to='standards.control')),
                ('evidence_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='control_links', to='evidence.evidenceitem')),
                ('linked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evidence_links', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-linked_at'],
                'unique_together': {('control', 'evidence_item')},
            },
        ),
        migrations.AddIndex(
            model_name='evidenceitem',
            index=models.Index(fields=['category', 'event_date'], name='evidence_it_category_0c1574_idx'),
        ),
        migrations.AddIndex(
            model_name='controlevidencelink',
            index=models.Index(fields=['control'], name='evidence_co_control_0d9b84_idx'),
        ),
        migrations.AddIndex(
            model_name='controlevidencelink',
            index=models.Index(fields=['evidence_item'], name='evidence_co_evidenc_8105d1_idx'),
        ),
    ]
