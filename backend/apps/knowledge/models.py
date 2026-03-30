from django.db import models


class Document(models.Model):
    """A document uploaded to ALFRED's knowledge base."""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    )

    title = models.CharField(max_length=300, blank=True)
    file = models.FileField(upload_to='documents/')
    filename = models.CharField(max_length=300)
    file_type = models.CharField(max_length=10, blank=True)
    file_size = models.IntegerField(default=0, help_text='Size in bytes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    chunk_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title or self.filename

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self.filename
        if self.file and not self.file_type:
            self.file_type = self.filename.rsplit('.', 1)[-1].lower() if '.' in self.filename else ''
        super().save(*args, **kwargs)
