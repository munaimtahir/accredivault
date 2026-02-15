import hashlib
import io
from datetime import timedelta

from django.conf import settings
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import CanExport, CanVerifyControls, CanViewAudit
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.compliance.engine import get_section_code_from_control, recompute_and_persist
from apps.compliance.export_service import generate_control_pdf_bytes, generate_controls_pdf_bytes
from apps.compliance.models import ComplianceAlert, ControlNote, ControlStatusCache, ControlVerification, ExportJob
from apps.compliance.serializers import (
    ComplianceAlertSerializer,
    ControlNoteSerializer,
    ControlStatusCacheSerializer,
    ControlVerificationSerializer,
    ExportJobSerializer,
)
from apps.evidence.models import ControlEvidenceLink
from apps.evidence.storage import get_s3_client
from apps.evidence.utils import create_audit_event
from apps.standards.models import Control, StandardPack


def _ensure_bucket_exists(s3_client, bucket_name: str):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except Exception:
        s3_client.create_bucket(Bucket=bucket_name)


def _export_download_payload(s3_client, bucket: str, object_key: str):
    expires_in = 600
    download_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': object_key},
        ExpiresIn=expires_in,
    )
    return {'url': download_url, 'expires_in': expires_in}


def _latest_pack_or_404():
    pack = StandardPack.objects.order_by('-created_at').first()
    if pack is None:
        return None
    return pack


def _run_export_job(request, job: ExportJob, object_key: str, pdf_bytes: bytes):
    s3_client = get_s3_client()
    _ensure_bucket_exists(s3_client, job.bucket)
    s3_client.upload_fileobj(
        io.BytesIO(pdf_bytes),
        job.bucket,
        object_key,
        ExtraArgs={'ContentType': 'application/pdf'},
    )

    job.status = ExportJob.STATUS_COMPLETED
    job.completed_at = timezone.now()
    job.object_key = object_key
    job.sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    job.size_bytes = len(pdf_bytes)
    job.save(update_fields=['status', 'completed_at', 'object_key', 'sha256', 'size_bytes'])

    create_audit_event(
        request=request,
        action='EXPORT_CREATED',
        entity_type='ExportJob',
        entity_id=job.id,
        after_json=ExportJobSerializer(job).data,
    )

    return {
        'job': ExportJobSerializer(job).data,
        'download': _export_download_payload(s3_client, job.bucket, object_key),
    }


class ControlStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, control_id):
        control = get_object_or_404(Control, pk=control_id)
        cache = recompute_and_persist(control)
        return Response(ControlStatusCacheSerializer(cache).data, status=status.HTTP_200_OK)


class ControlVerifyView(APIView):
    permission_classes = [CanVerifyControls]
    verification_status = ControlVerification.STATUS_VERIFIED
    audit_action = 'CONTROL_VERIFIED'

    def post(self, request, control_id):
        control = get_object_or_404(Control, pk=control_id)
        latest_linked_at = (
            ControlEvidenceLink.objects
            .filter(control=control)
            .order_by('-linked_at')
            .values_list('linked_at', flat=True)
            .first()
        )

        verification = ControlVerification.objects.create(
            control=control,
            status=self.verification_status,
            remarks=request.data.get('remarks'),
            verified_by=(request.user if request.user.is_authenticated else None),
            evidence_snapshot_at=latest_linked_at,
        )
        create_audit_event(
            request=request,
            action=self.audit_action,
            entity_type='ControlVerification',
            entity_id=verification.id,
            after_json=ControlVerificationSerializer(verification).data,
        )

        cache = recompute_and_persist(control)
        return Response(
            {
                'verification': ControlVerificationSerializer(verification).data,
                'status_cache': ControlStatusCacheSerializer(cache).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ControlRejectView(ControlVerifyView):
    verification_status = ControlVerification.STATUS_REJECTED
    audit_action = 'CONTROL_REJECTED'


class ControlExportView(APIView):
    permission_classes = [CanExport]

    def get(self, request, control_id):
        control = get_object_or_404(Control, pk=control_id)
        jobs = ExportJob.objects.filter(
            control=control,
            job_type=ExportJob.JOB_CONTROL_PDF,
        ).order_by('-created_at')
        return Response(ExportJobSerializer(jobs, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, control_id):
        control = get_object_or_404(Control, pk=control_id)
        pack = control.standard_pack
        bucket = getattr(settings, 'MINIO_BUCKET_EXPORTS', 'exports')
        placeholder_key = f"exports/pending/{timezone.now().strftime('%Y%m%d%H%M%S')}-{control.id}.pdf"

        job = ExportJob.objects.create(
            job_type=ExportJob.JOB_CONTROL_PDF,
            status=ExportJob.STATUS_RUNNING,
            standard_pack=pack,
            control=control,
            filters_json={},
            created_by=(request.user if request.user.is_authenticated else None),
            bucket=bucket,
            object_key=placeholder_key,
            filename=f'{control.control_code}-evidence-pack.pdf',
        )
        object_key = f'exports/{pack.authority_code}/{pack.version}/controls/{control.control_code}/{job.id}.pdf'

        try:
            payload = _run_export_job(
                request=request,
                job=job,
                object_key=object_key,
                pdf_bytes=generate_control_pdf_bytes(control),
            )
            return Response(payload, status=status.HTTP_201_CREATED)
        except Exception as exc:
            job.status = ExportJob.STATUS_FAILED
            job.error_text = str(exc)
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_text', 'completed_at'])
            return Response(
                {'detail': 'Export failed', 'job': ExportJobSerializer(job).data},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SectionExportView(APIView):
    permission_classes = [CanExport]

    def post(self, request, section_code):
        pack = _latest_pack_or_404()
        if pack is None:
            return Response({'detail': 'No standard pack found'}, status=status.HTTP_404_NOT_FOUND)

        normalized_code = section_code.strip().upper()
        controls = list(pack.controls.filter(control_code__icontains=f'-{normalized_code}-').order_by('sort_order'))
        if not controls:
            return Response({'detail': 'No controls found for section'}, status=status.HTTP_404_NOT_FOUND)

        bucket = getattr(settings, 'MINIO_BUCKET_EXPORTS', 'exports')
        placeholder_key = f"exports/pending/{timezone.now().strftime('%Y%m%d%H%M%S')}-section-{normalized_code}.pdf"
        job = ExportJob.objects.create(
            job_type=ExportJob.JOB_SECTION_PACK,
            status=ExportJob.STATUS_RUNNING,
            standard_pack=pack,
            section_code=normalized_code,
            filters_json={'section_code': normalized_code},
            created_by=(request.user if request.user.is_authenticated else None),
            bucket=bucket,
            object_key=placeholder_key,
            filename=f'{pack.authority_code}-{pack.version}-section-{normalized_code}.pdf',
        )
        object_key = f'exports/{pack.authority_code}/{pack.version}/sections/{normalized_code}/{job.id}.pdf'

        try:
            pdf_bytes = generate_controls_pdf_bytes(
                pack=pack,
                controls=controls,
                title=f'Section Pack - {normalized_code}',
                section_code=normalized_code,
            )
            payload = _run_export_job(request=request, job=job, object_key=object_key, pdf_bytes=pdf_bytes)
            return Response(payload, status=status.HTTP_201_CREATED)
        except Exception as exc:
            job.status = ExportJob.STATUS_FAILED
            job.error_text = str(exc)
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_text', 'completed_at'])
            return Response(
                {'detail': 'Section export failed', 'job': ExportJobSerializer(job).data},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FullPackExportView(APIView):
    permission_classes = [CanExport]

    def post(self, request):
        pack = _latest_pack_or_404()
        if pack is None:
            return Response({'detail': 'No standard pack found'}, status=status.HTTP_404_NOT_FOUND)

        controls = list(pack.controls.order_by('sort_order'))
        if not controls:
            return Response({'detail': 'No controls found in selected pack'}, status=status.HTTP_404_NOT_FOUND)

        bucket = getattr(settings, 'MINIO_BUCKET_EXPORTS', 'exports')
        placeholder_key = f"exports/pending/{timezone.now().strftime('%Y%m%d%H%M%S')}-full.pdf"
        job = ExportJob.objects.create(
            job_type=ExportJob.JOB_FULL_PACK,
            status=ExportJob.STATUS_RUNNING,
            standard_pack=pack,
            filters_json={},
            created_by=(request.user if request.user.is_authenticated else None),
            bucket=bucket,
            object_key=placeholder_key,
            filename=f'{pack.authority_code}-{pack.version}-full-pack.pdf',
        )
        object_key = f'exports/{pack.authority_code}/{pack.version}/full/{job.id}.pdf'

        try:
            pdf_bytes = generate_controls_pdf_bytes(
                pack=pack,
                controls=controls,
                title=f'Full Pack - {pack.authority_code} {pack.version}',
            )
            payload = _run_export_job(request=request, job=job, object_key=object_key, pdf_bytes=pdf_bytes)
            return Response(payload, status=status.HTTP_201_CREATED)
        except Exception as exc:
            job.status = ExportJob.STATUS_FAILED
            job.error_text = str(exc)
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_text', 'completed_at'])
            return Response(
                {'detail': 'Full export failed', 'job': ExportJobSerializer(job).data},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExportDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = get_object_or_404(ExportJob, pk=job_id)
        if job.status != ExportJob.STATUS_COMPLETED:
            return Response({'detail': 'Export is not completed.'}, status=status.HTTP_400_BAD_REQUEST)

        s3_client = get_s3_client()
        return Response(_export_download_payload(s3_client, job.bucket, job.object_key), status=status.HTTP_200_OK)


class DashboardSummaryView(APIView):
    permission_classes = [CanViewAudit]

    def get(self, request):
        pack = _latest_pack_or_404()
        if pack is None:
            return Response({'detail': 'No standard pack found'}, status=status.HTTP_404_NOT_FOUND)

        controls = list(pack.controls.select_related('status_cache').order_by('sort_order'))
        today = timezone.localdate()
        near_due_cutoff = today + timedelta(days=14)

        totals = {
            'total_controls': len(controls),
            'NOT_STARTED': 0,
            'IN_PROGRESS': 0,
            'READY': 0,
            'VERIFIED': 0,
            'OVERDUE': 0,
            'NEAR_DUE': 0,
        }
        section_totals = {}
        upcoming_due = []

        for control in controls:
            cache = getattr(control, 'status_cache', None)
            status_name = cache.computed_status if cache else 'NOT_STARTED'
            totals[status_name] = totals.get(status_name, 0) + 1

            section_code = get_section_code_from_control(control.control_code)
            if section_code not in section_totals:
                section_totals[section_code] = {
                    'section_code': section_code,
                    'total': 0,
                    'READY': 0,
                    'VERIFIED': 0,
                    'OVERDUE': 0,
                }
            section_totals[section_code]['total'] += 1
            if status_name in ('READY', 'VERIFIED', 'OVERDUE'):
                section_totals[section_code][status_name] += 1

            if cache and cache.next_due_date and status_name != 'OVERDUE' and today <= cache.next_due_date <= near_due_cutoff:
                totals['NEAR_DUE'] += 1
                upcoming_due.append(
                    {
                        'control_id': control.id,
                        'control_code': control.control_code,
                        'section_code': section_code,
                        'next_due_date': cache.next_due_date,
                    }
                )

        last_computed_at = (
            ControlStatusCache.objects
            .filter(control__standard_pack=pack)
            .aggregate(value=Max('computed_at'))
            .get('value')
        )

        upcoming_due.sort(key=lambda row: row['next_due_date'])

        return Response(
            {
                'pack_version': pack.version,
                'totals': totals,
                'sections': sorted(section_totals.values(), key=lambda row: row['section_code']),
                'upcoming_due': upcoming_due[:20],
                'last_computed_at': last_computed_at,
            },
            status=status.HTTP_200_OK,
        )


class AlertsListView(APIView):
    permission_classes = [CanViewAudit]

    def get(self, request):
        alerts = (
            ComplianceAlert.objects
            .filter(cleared_at__isnull=True)
            .select_related('control')
            .order_by('-triggered_at')
        )
        return Response(ComplianceAlertSerializer(alerts, many=True).data, status=status.HTTP_200_OK)


class ControlNotesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, control_id):
        control = get_object_or_404(Control, pk=control_id)
        notes = control.notes.select_related('created_by', 'resolved_by').all()
        return Response(ControlNoteSerializer(notes, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, control_id):
        if not CanVerifyControls().has_permission(request, self):
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        control = get_object_or_404(Control, pk=control_id)
        serializer = ControlNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save(
            control=control,
            created_by=(request.user if request.user.is_authenticated else None),
        )
        create_audit_event(
            request=request,
            action='CONTROL_NOTE_CREATED',
            entity_type='ControlNote',
            entity_id=note.id,
            after_json=ControlNoteSerializer(note).data,
        )
        return Response(ControlNoteSerializer(note).data, status=status.HTTP_201_CREATED)


class ControlNoteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, control_id, note_id):
        if not CanVerifyControls().has_permission(request, self):
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        note = get_object_or_404(ControlNote, pk=note_id, control_id=control_id)
        before_data = ControlNoteSerializer(note).data

        allowed_fields = {'note_type', 'text', 'resolved'}
        updates = {k: v for k, v in request.data.items() if k in allowed_fields}

        if 'note_type' in updates:
            note.note_type = updates['note_type']
        if 'text' in updates:
            note.text = updates['text']
        if 'resolved' in updates:
            resolved = bool(updates['resolved'])
            if resolved and not note.resolved:
                note.resolved = True
                note.resolved_at = timezone.now()
                note.resolved_by = request.user if request.user.is_authenticated else None
            elif not resolved and note.resolved:
                note.resolved = False
                note.resolved_at = None
                note.resolved_by = None

        note.save()
        after_data = ControlNoteSerializer(note).data
        create_audit_event(
            request=request,
            action='CONTROL_NOTE_UPDATED',
            entity_type='ControlNote',
            entity_id=note.id,
            before_json=before_data,
            after_json=after_data,
        )
        return Response(after_data, status=status.HTTP_200_OK)

    def delete(self, request, control_id, note_id):
        if not CanVerifyControls().has_permission(request, self):
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        note = get_object_or_404(ControlNote, pk=note_id, control_id=control_id)
        before_data = ControlNoteSerializer(note).data
        note.delete()
        create_audit_event(
            request=request,
            action='CONTROL_NOTE_DELETED',
            entity_type='ControlNote',
            entity_id=note_id,
            before_json=before_data,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
