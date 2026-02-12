import hashlib
import io

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.compliance.engine import compute_control_status, fetch_linked_evidence, recompute_and_persist
from apps.compliance.models import ControlVerification, ExportJob
from apps.compliance.serializers import (
    ControlStatusCacheSerializer,
    ControlVerificationSerializer,
    ExportJobSerializer,
)
from apps.evidence.models import ControlEvidenceLink
from apps.evidence.storage import get_s3_client
from apps.evidence.utils import create_audit_event
from apps.standards.models import Control


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(page_count)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.setFont('Helvetica', 9)
        self.setFillColor(colors.grey)
        self.drawRightString(200 * mm, 10 * mm, f"Page {self._pageNumber} of {page_count}")


def _safe_text(value):
    if value is None:
        return '-'
    return str(value)


def _ensure_bucket_exists(s3_client, bucket_name: str):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except Exception:
        s3_client.create_bucket(Bucket=bucket_name)


def _generate_control_pdf_bytes(control: Control) -> bytes:
    styles = getSampleStyleSheet()
    normal = styles['Normal']
    heading = styles['Heading2']

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    status_data = compute_control_status(control)
    evidence_items = list(fetch_linked_evidence(control))

    story = []
    story.append(Paragraph('AccrediVault / PHC Licensing Evidence Pack', styles['Title']))
    story.append(Spacer(1, 8))

    pack = control.standard_pack
    generated_at = timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    pack_table = Table([
        ['Authority', _safe_text(pack.authority_code)],
        ['Pack Version', _safe_text(pack.version)],
        ['Generated At', generated_at],
    ], colWidths=[45 * mm, 120 * mm])
    pack_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(pack_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph('Control', heading))
    control_table = Table([
        ['Control Code', _safe_text(control.control_code)],
        ['Section', _safe_text(control.section)],
        ['Standard', _safe_text(control.standard)],
        ['Indicator', _safe_text(control.indicator)],
    ], colWidths=[45 * mm, 120 * mm])
    control_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(control_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph('Current Status', heading))
    status_table = Table([
        ['Computed Status', status_data['computed_status']],
        ['Last Evidence Date', _safe_text(status_data['last_evidence_date'])],
        ['Next Due Date', _safe_text(status_data['next_due_date'])],
    ], colWidths=[45 * mm, 120 * mm])
    status_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph('Evidence Items', heading))
    if not evidence_items:
        story.append(Paragraph('No evidence linked.', normal))
    else:
        for idx, ev in enumerate(evidence_items, start=1):
            story.append(Paragraph(f"{idx}. {_safe_text(ev.title)}", styles['Heading4']))
            ev_table = Table([
                ['Event Date', _safe_text(ev.event_date), 'Category', _safe_text(ev.category)],
                ['Subtype', _safe_text(ev.subtype), 'Valid From', _safe_text(ev.valid_from)],
                ['Valid Until', _safe_text(ev.valid_until), 'Notes', _safe_text(ev.notes)],
            ], colWidths=[30 * mm, 60 * mm, 30 * mm, 45 * mm])
            ev_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
                ('BACKGROUND', (2, 0), (2, -1), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(ev_table)

            if ev.files.exists():
                file_rows = [['Filename', 'SHA256', 'Uploaded At']]
                for evidence_file in ev.files.all().order_by('-uploaded_at'):
                    uploaded = evidence_file.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
                    file_rows.append([evidence_file.filename, evidence_file.sha256, uploaded])
                files_table = Table(file_rows, colWidths=[52 * mm, 73 * mm, 40 * mm])
                files_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ECEFF4')),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(Spacer(1, 4))
                story.append(files_table)
            else:
                story.append(Paragraph('Attached files: none', normal))

            story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()


class ControlStatusView(APIView):
    def get(self, request, control_id):
        control = get_object_or_404(Control, pk=control_id)
        cache = recompute_and_persist(control)
        return Response(ControlStatusCacheSerializer(cache).data, status=status.HTTP_200_OK)


class ControlVerifyView(APIView):
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
        filename = f"{control.control_code}-evidence-pack.pdf"

        job = ExportJob.objects.create(
            job_type=ExportJob.JOB_CONTROL_PDF,
            status=ExportJob.STATUS_RUNNING,
            standard_pack=pack,
            control=control,
            filters_json={},
            created_by=(request.user if request.user.is_authenticated else None),
            bucket=bucket,
            object_key=placeholder_key,
            filename=filename,
        )

        object_key = f"exports/{pack.authority_code}/{pack.version}/controls/{control.control_code}/{job.id}.pdf"

        try:
            pdf_bytes = _generate_control_pdf_bytes(control)
            sha256 = hashlib.sha256(pdf_bytes).hexdigest()
            size_bytes = len(pdf_bytes)

            s3_client = get_s3_client()
            _ensure_bucket_exists(s3_client, bucket)
            s3_client.upload_fileobj(
                io.BytesIO(pdf_bytes),
                bucket,
                object_key,
                ExtraArgs={'ContentType': 'application/pdf'},
            )

            job.status = ExportJob.STATUS_COMPLETED
            job.completed_at = timezone.now()
            job.object_key = object_key
            job.sha256 = sha256
            job.size_bytes = size_bytes
            job.save(update_fields=['status', 'completed_at', 'object_key', 'sha256', 'size_bytes'])

            create_audit_event(
                request=request,
                action='EXPORT_CREATED',
                entity_type='ExportJob',
                entity_id=job.id,
                after_json=ExportJobSerializer(job).data,
            )

            expires_in = 600
            download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_key},
                ExpiresIn=expires_in,
            )
            return Response(
                {
                    'job': ExportJobSerializer(job).data,
                    'download': {'url': download_url, 'expires_in': expires_in},
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            job.status = ExportJob.STATUS_FAILED
            job.error_text = str(exc)
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_text', 'completed_at'])
            return Response(
                {'detail': 'Export failed', 'job': ExportJobSerializer(job).data},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExportDownloadView(APIView):
    def get(self, request, job_id):
        job = get_object_or_404(ExportJob, pk=job_id)
        if job.status != ExportJob.STATUS_COMPLETED:
            return Response({'detail': 'Export is not completed.'}, status=status.HTTP_400_BAD_REQUEST)

        s3_client = get_s3_client()
        expires_in = 600
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': job.bucket, 'Key': job.object_key},
            ExpiresIn=expires_in,
        )
        return Response({'url': url, 'expires_in': expires_in}, status=status.HTTP_200_OK)
