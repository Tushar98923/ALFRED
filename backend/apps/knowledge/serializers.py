from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'filename', 'file_type', 'file_size',
            'status', 'chunk_count', 'error_message',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'filename', 'file_type', 'file_size',
            'status', 'chunk_count', 'error_message',
            'created_at', 'updated_at',
        ]


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document file uploads."""
    file = serializers.FileField()
    title = serializers.CharField(required=False, allow_blank=True, max_length=300)
