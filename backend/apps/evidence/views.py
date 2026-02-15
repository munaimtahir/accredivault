from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import EvidenceItem, EvidenceFile, ControlEvidenceLink
from .serializers import EvidenceItemSerializer, EvidenceFileSerializer, ControlEvidenceLinkSerializer
from .storage import get_s3_client, build_object_key, compute_sha256
from .utils import create_audit_event
from apps.users.permissions import CanReadControls, CanWriteEvidence
from apps.compliance.engine import recompute_and_persist
from apps.standards.models import Control
from apps.standards.serializers import ControlSerializer


class EvidenceItemCreateView(APIView):
    permission_classes = [CanWriteEvidence]

    def post(self, request):
        serializer = EvidenceItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evidence_item = serializer.save(
            created_by=(request.user if request.user.is_authenticated else None)
        )
        response_data = EvidenceItemSerializer(evidence_item).data
        create_audit_event(
            request=request,
            action='EVIDENCE_CREATED',
            entity_type='EvidenceItem',
            entity_id=evidence_item.id,
            after_json=response_data,
        )
        return Response(response_data, status=status.HTTP_201_CREATED)


class EvidenceFileUploadView(APIView):
    permission_classes = [CanWriteEvidence]

    def post(self, request, evidence_item_id):
        evidence_item = get_object_or_404(EvidenceItem, pk=evidence_item_id)
        files = request.FILES.getlist('files')
        if not files and 'file' in request.FILES:
            files = [request.FILES['file']]

        if not files:
            return Response({'detail': 'No files provided.'}, status=status.HTTP_400_BAD_REQUEST)

        bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'evidence')
        s3_client = get_s3_client()
        created_files = []

        for uploaded_file in files:
            object_key = build_object_key(evidence_item.id, uploaded_file.name)
            sha256 = compute_sha256(uploaded_file)
            try:
                uploaded_file.seek(0)
            except Exception:
                pass

            content_type = uploaded_file.content_type or 'application/octet-stream'
            s3_client.upload_fileobj(
                uploaded_file,
                bucket,
                object_key,
                ExtraArgs={'ContentType': content_type},
            )

            evidence_file = EvidenceFile.objects.create(
                evidence_item=evidence_item,
                bucket=bucket,
                object_key=object_key,
                filename=uploaded_file.name,
                content_type=content_type,
                size_bytes=uploaded_file.size,
                sha256=sha256,
            )
            evidence_file_data = EvidenceFileSerializer(evidence_file).data
            created_files.append(evidence_file_data)
            create_audit_event(
                request=request,
                action='EVIDENCE_FILE_UPLOADED',
                entity_type='EvidenceFile',
                entity_id=evidence_file.id,
                after_json=evidence_file_data,
            )

        return Response({'files': created_files}, status=status.HTTP_201_CREATED)


class EvidenceFileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        evidence_file = get_object_or_404(EvidenceFile, pk=file_id)
        s3_client = get_s3_client()
        expires_in = 600
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': evidence_file.bucket, 'Key': evidence_file.object_key},
            ExpiresIn=expires_in,
        )
        return Response({'url': url, 'expires_in': expires_in}, status=status.HTTP_200_OK)


class ControlEvidenceLinkView(APIView):
    permission_classes = [CanWriteEvidence]

    def post(self, request, control_id):
        control = get_object_or_404(Control, pk=control_id)
        evidence_item_id = request.data.get('evidence_item_id')
        if not evidence_item_id:
            return Response({'detail': 'evidence_item_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        evidence_item = get_object_or_404(EvidenceItem, pk=evidence_item_id)
        note = request.data.get('note')
        link, created = ControlEvidenceLink.objects.get_or_create(
            control=control,
            evidence_item=evidence_item,
            defaults={
                'relevance_note': note,
                'linked_by': (request.user if request.user.is_authenticated else None),
            },
        )
        if not created and note is not None:
            link.relevance_note = note
            link.save(update_fields=['relevance_note'])

        response_data = ControlEvidenceLinkSerializer(link).data
        if created:
            create_audit_event(
                request=request,
                action='EVIDENCE_LINKED',
                entity_type='ControlEvidenceLink',
                entity_id=link.id,
                after_json=response_data,
            )
            recompute_and_persist(control)
        return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ControlEvidenceUnlinkView(APIView):
    permission_classes = [CanWriteEvidence]

    def delete(self, request, control_id, link_id):
        link = get_object_or_404(ControlEvidenceLink, pk=link_id, control_id=control_id)
        before_data = ControlEvidenceLinkSerializer(link).data
        link.delete()
        create_audit_event(
            request=request,
            action='EVIDENCE_UNLINKED',
            entity_type='ControlEvidenceLink',
            entity_id=link_id,
            before_json=before_data,
        )
        control = link.control
        recompute_and_persist(control)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ControlTimelineView(APIView):
    permission_classes = [CanReadControls]

    def get(self, request, control_id):
        control = get_object_or_404(Control, pk=control_id)
        links = (
            ControlEvidenceLink.objects
            .select_related('evidence_item')
            .prefetch_related('evidence_item__files')
            .filter(control=control)
            .order_by('-evidence_item__event_date', '-evidence_item__created_at')
        )
        link_data = ControlEvidenceLinkSerializer(links, many=True).data
        response_data = {
            'control': ControlSerializer(control).data,
            'evidence_items': link_data,
        }
        return Response(response_data, status=status.HTTP_200_OK)
