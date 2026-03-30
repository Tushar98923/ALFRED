import os
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
from rag.pipeline import ingest_document, query_knowledge, delete_document, get_knowledge_stats
from rag.loaders import SUPPORTED_EXTENSIONS


# Max upload size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD for knowledge base documents."""
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def perform_destroy(self, instance):
        """When deleting a document, also remove its chunks from the vector store."""
        delete_document(instance.filename)
        # Delete the actual file
        if instance.file and os.path.exists(instance.file.path):
            os.remove(instance.file.path)
        instance.delete()


@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    """
    Upload a document to the knowledge base.
    Accepts multipart form data with a 'file' field.
    """
    serializer = DocumentUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = serializer.validated_data['file']
    title = serializer.validated_data.get('title', '') or uploaded_file.name

    # Validate file extension
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return Response(
            {'error': f'Unsupported file type: {ext}. Supported: {", ".join(sorted(SUPPORTED_EXTENSIONS))}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate file size
    if uploaded_file.size > MAX_FILE_SIZE:
        return Response(
            {'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create the Document record
    doc = Document.objects.create(
        title=title,
        file=uploaded_file,
        filename=uploaded_file.name,
        file_size=uploaded_file.size,
        status='processing',
    )

    # Run the ingestion pipeline
    try:
        result = ingest_document(
            file_path=doc.file.path,
            source_name=doc.filename,
        )

        doc.status = result['status']
        doc.chunk_count = result.get('chunk_count', 0)
        if result.get('error'):
            doc.error_message = result['error']
        doc.save()
    except Exception as e:
        doc.status = 'error'
        doc.error_message = str(e)
        doc.save()
        return Response(
            {'error': f'Ingestion failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['POST'])
@parser_classes([JSONParser])
def query_knowledge_view(request):
    """
    Query the knowledge base using RAG.
    Accepts JSON: { "text": "your question here" }
    """
    text = request.data.get('text', '').strip()
    if not text:
        return Response(
            {'error': 'text is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = query_knowledge(text)
        return Response(result)
    except Exception as e:
        return Response(
            {'error': f'Query failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
def knowledge_stats(request):
    """Return stats about the knowledge base."""
    stats = get_knowledge_stats()
    stats['document_count'] = Document.objects.filter(status='ready').count()
    return Response(stats)
