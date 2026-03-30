from django.db import models


class Conversation(models.Model):
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self) -> str:
        return self.title or f"Conversation {self.pk}"


class Message(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:40]}"


class LLMProvider(models.Model):
    """Stores API keys for different LLM providers."""

    PROVIDER_CHOICES = (
        ('gemini', 'Google Gemini'),
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('lmstudio', 'LM Studio (Local)'),
        ('openrouter', 'OpenRouter'),
    )

    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, unique=True)
    api_key = models.CharField(max_length=500, blank=True)
    base_url = models.CharField(max_length=500, blank=True, help_text='Custom API base URL (for LM Studio, etc.)')
    model_name = models.CharField(max_length=200, blank=True, help_text='Preferred model name')
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider']

    def __str__(self) -> str:
        status = '✓' if self.is_active else '✗'
        return f"[{status}] {self.get_provider_display()}"

    @property
    def is_configured(self) -> bool:
        if self.provider == 'lmstudio':
            return bool(self.base_url)
        return bool(self.api_key)

    @property
    def masked_key(self) -> str:
        if not self.api_key:
            return ''
        if len(self.api_key) <= 8:
            return '••••••••'
        return self.api_key[:4] + '•' * (len(self.api_key) - 8) + self.api_key[-4:]
