from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.parsers import JSONParser
import os
import google.generativeai as genai
import subprocess
from typing import List
from rest_framework import viewsets
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY') 
genai.configure(api_key=_api_key)

@csrf_exempt
@require_POST
def command_view(request):
    try:
        data = JSONParser().parse(request)
        user_text = data.get('text')
        conversation_id = data.get('conversation_id')
        if not user_text:
            return JsonResponse({'error': 'text is required'}, status=400)

        prompt = (
            "You are a Windows command generator. Given a natural language task, "
            "return ONLY a safe PowerShell command that accomplishes it. "
            "If risky or requires confirmation, return a no-op echo with instructions.\n\n"
            f"Task: {user_text}\nCommand:"
        )

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        command = (response.text or '').strip()

        convo = None
        if conversation_id:
            try:
                convo = Conversation.objects.get(pk=conversation_id)
            except Conversation.DoesNotExist:
                convo = Conversation.objects.create(title=user_text[:40])
        else:
            convo = Conversation.objects.create(title=user_text[:40])

        Message.objects.create(conversation=convo, role='user', content=user_text)
        Message.objects.create(conversation=convo, role='assistant', content=command)

        return JsonResponse({'command': command, 'conversation_id': convo.id})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)


SAFE_POWERSHELL_COMMANDS: List[str] = [
    'echo', 'mkdir', 'new-item', 'ni', 'ls', 'dir', 'copy', 'cp', 'move', 'mv', 'remove-item', 'ri', 'del', 'rmdir', 'type'
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
                'error': 'Command not allowed for safety. Use echo or other safe commands.',
                'allowed': SAFE_POWERSHELL_COMMANDS,
            }, status=400)

        full_cmd = [
            'powershell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-Command', command_text
        ]
        completed = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=15,
            shell=False
        )
        return JsonResponse({
            'returncode': completed.returncode,
            'stdout': completed.stdout,
            'stderr': completed.stderr,
        }, status=200)
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


