from rest_framework import serializers
from .models import Conversation, Message, LLMProvider


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "conversation", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at", "messages", "message_count"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_message_count(self, obj):
        return obj.messages.count()


class LLMProviderSerializer(serializers.ModelSerializer):
    masked_key = serializers.CharField(read_only=True)
    is_configured = serializers.BooleanField(read_only=True)
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)

    class Meta:
        model = LLMProvider
        fields = [
            'id', 'provider', 'provider_display', 'api_key', 'base_url',
            'model_name', 'is_active', 'is_configured', 'masked_key',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'masked_key', 'is_configured', 'provider_display', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True},  # Never return the raw key
        }
