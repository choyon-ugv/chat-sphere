from django.db import models
from django.utils import timezone

class Participant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - {'Online' if self.online else 'Offline'}"

class Conversation(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    participants = models.ManyToManyField(Participant, related_name='conversations')
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or f"Conversation {self.id}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(Participant, related_name='read_messages', blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.sender.name}: {self.content[:50]}"
    
