from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import viewsets, status
import os
import google.generativeai as genai
import subprocess
from typing import List
from .models import Conversation, Message, LLMProvider
from .serializers import ConversationSerializer, MessageSerializer, LLMProviderSerializer

def _detect_and_route(user_text: str, conversation_id=None):
    """Auto-detect whether the user wants a system command or a knowledge answer."""
    from rag.intent import classify_intent
    from rag.pipeline import query_knowledge, get_knowledge_stats

    stats = get_knowledge_stats()
    has_kb = stats.get('total_chunks', 0) > 0
    intent = classify_intent(user_text, has_knowledge_base=has_kb)

    if intent == 'knowledge':
        result = query_knowledge(user_text)
        return {
            'mode': 'knowledge',
            'answer': result['answer'],
            'sources': result.get('sources', []),
            'chunks_retrieved': result.get('chunks_retrieved', 0),
        }
    return {'mode': 'command'}


@csrf_exempt
@require_POST
def command_view(request):
    try:
        data = JSONParser().parse(request)
        user_text = data.get('text')
        conversation_id = data.get('conversation_id')
        if not user_text:
            return JsonResponse({'error': 'text is required'}, status=400)

        route = _detect_and_route(user_text, conversation_id)

        # Get or create conversation
        convo = None
        if conversation_id:
            try:
                convo = Conversation.objects.get(pk=conversation_id)
            except Conversation.DoesNotExist:
                convo = Conversation.objects.create(title=user_text[:40])
        else:
            convo = Conversation.objects.create(title=user_text[:40])

        Message.objects.create(conversation=convo, role='user', content=user_text)

        if route['mode'] == 'knowledge':
            answer = route['answer']
            Message.objects.create(conversation=convo, role='assistant', content=answer)
            return JsonResponse({
                'mode': 'knowledge',
                'answer': answer,
                'sources': route.get('sources', []),
                'chunks_retrieved': route.get('chunks_retrieved', 0),
                'conversation_id': convo.id,
            })
        else:
            prompt = (
                "You are a Windows command generator. Given a natural language task, "
                "return ONLY a safe PowerShell command that accomplishes it. "
                "If risky or requires confirmation, return a no-op echo with instructions.\n\n"
                f"Task: {user_text}\nCommand:"
            )
            from rag.model_resolver import get_model
            model = get_model()
            response = model.generate_content(prompt)
            command = (response.text or '').strip()
            Message.objects.create(conversation=convo, role='assistant', content=command)
            return JsonResponse({
                'mode': 'command',
                'command': command,
                'conversation_id': convo.id,
            })
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)


SAFE_POWERSHELL_COMMANDS: List[str] = [
    'echo', 'mkdir', 'new-item', 'ni', 'ls', 'dir', 'copy', 'cp',
    'move', 'mv', 'remove-item', 'ri', 'del', 'rmdir', 'type',
]


def _is_safe_command_ps(command_text: str) -> bool:
    token = command_text.strip().split()[0].lower() if command_text.strip() else ''
    return token in SAFE_POWERSHELL_COMMANDS


@csrf_exempt
@require_POST
def execute_view(request):
    try:
        data = JSONParser().parse(request)
        command_text = data.get('command')
        if not command_text:
            return JsonResponse({'error': 'command is required'}, status=400)

        if not _is_safe_command_ps(command_text):
            return JsonResponse({
                'error': 'Command not allowed for safety.',
                'allowed': SAFE_POWERSHELL_COMMANDS,
            }, status=400)

        full_cmd = [
            'powershell', '-NoProfile', '-NonInteractive',
            '-ExecutionPolicy', 'Bypass', '-Command', command_text,
        ]
        completed = subprocess.run(
            full_cmd, capture_output=True, text=True, timeout=15, shell=False,
        )
        return JsonResponse({
            'returncode': completed.returncode,
            'stdout': completed.stdout,
            'stderr': completed.stderr,
        })
    except subprocess.TimeoutExpired:
        return JsonResponse({'error': 'Command timed out'}, status=504)
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all().order_by('-updated_at')
    serializer_class = ConversationSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-created_at')
    serializer_class = MessageSerializer


class LLMProviderViewSet(viewsets.ModelViewSet):
    queryset = LLMProvider.objects.all()
    serializer_class = LLMProviderSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Set this provider as the active one (deactivates others of the same provider type)."""
        provider = self.get_object()
        if not provider.is_configured:
            return Response(
                {'error': 'Provider is not configured. Add an API key or base URL first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Deactivate all others
        LLMProvider.objects.exclude(pk=provider.pk).update(is_active=False)
        provider.is_active = True
        provider.save()
        return Response(LLMProviderSerializer(provider).data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        """List all available provider choices."""
        return Response([
            {'value': c[0], 'label': c[1]}
            for c in LLMProvider.PROVIDER_CHOICES
        ])
