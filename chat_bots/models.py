from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Participant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='participant')
    online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.online else 'Offline'}"

class Conversation(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    participants = models.ManyToManyField(Participant, related_name='conversations')
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.name:
            return self.name
        return " & ".join([p.user.username for p in self.participants.all()[:2]])

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(Participant, related_name='read_messages', blank=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.sender.user.username}: {self.content[:50]}"