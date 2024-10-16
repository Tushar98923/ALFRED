from django.shortcuts import render

import openai
from django.http import JsonResponse

openai.api_key = 'openaikey'

def send_to_chatgpt(request):
    if request.method == 'POST':
        command = request.POST.get('command')

        try:
            response = openai.Completion.create(
                model="gpt-3.5-turbo",
                prompt=command,
                max_tokens=150
            )
            chatgpt_response = response.choices[0].text.strip()
            return JsonResponse({'response': chatgpt_response})
        except Exception as e:
            return JsonResponse({'error': str(e)})

