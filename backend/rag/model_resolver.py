"""
Provides an abstracted model interface that supports:
1. Google Gemini via `google.generativeai`
2. OpenAI-compatible APIs (OpenAI, LM Studio, OpenRouter) via `openai`
"""
import os
from dataclasses import dataclass
from typing import Optional

# Setup environment fallback
_env_gemini = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
_env_openai = os.getenv('OPENAI_API_KEY')


@dataclass
class GenerateResult:
    """Standardized response object reflecting the structure of Gemini's response.text"""
    text: str


class GenericModel:
    """A unified wrapper around different LLM providers"""
    
    def __init__(self, provider: str, api_key: str, base_url: str = "", model_name: str = ""):
        self.provider = provider
        self.api_key = api_key or "sk-no-key-required"  # LM Studio often doesn't need a key
        
        # Sanitize the base URL (remove trailing slashes, spaces, and full endpoint paths)
        clean_url = (base_url or "").strip().rstrip('/')
        if clean_url.endswith('/chat/completions'):
            clean_url = clean_url[:-17]  # remove the /chat/completions part
        self.base_url = clean_url

        self.model_name = model_name

        if self.provider == 'gemini':
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._gemini_model = genai.GenerativeModel(self.model_name or self._get_best_gemini())
        else:
            # For OpenAI, LM Studio, Anthropic (via proxy), OpenRouter
            from openai import OpenAI
            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs['base_url'] = self.base_url
            self._openai_client = OpenAI(**client_kwargs)

    def _get_best_gemini(self):
        return 'gemini-2.0-flash'

    def generate_content(self, prompt: str) -> GenerateResult:
        if self.provider == 'gemini':
            response = self._gemini_model.generate_content(prompt)
            return GenerateResult(text=response.text or '')
        
        else:
            # Provide a fallback model name if none specified
            model_to_use = self.model_name
            if not model_to_use:
                try:
                    # Auto-detect the first available model on the server
                    available_models = self._openai_client.models.list()
                    if available_models and available_models.data:
                        model_to_use = available_models.data[0].id
                except Exception:
                    pass
            
            model_to_use = model_to_use or "gpt-3.5-turbo"
            
            response = self._openai_client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return GenerateResult(text=response.choices[0].message.content or '')


def get_model() -> GenericModel:
    """
    Looks up the active LLM Provider from the database and returns a configured model wrapper.
    If no active provider, falls back to environment variables.
    """
    try:
        from apps.assistant.models import LLMProvider
        active = LLMProvider.objects.filter(is_active=True).first()
        if active:
            return GenericModel(
                provider=active.provider,
                api_key=active.api_key,
                base_url=active.base_url,
                model_name=active.model_name
            )
    except Exception:
        # Fails gracefully if Django isn't loaded or DB isn't migrated
        pass

    # Fallback to pure environment variables
    if _env_gemini:
        return GenericModel(provider='gemini', api_key=_env_gemini, model_name='gemini-2.0-flash')
    elif _env_openai:
        return GenericModel(provider='openai', api_key=_env_openai, model_name='gpt-4o')

    # Desperate fallback returning dummy error message if no config exists
    raise ValueError("No LLM Providers configured. Please add an API key in Settings.")
