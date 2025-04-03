from rest_framework import serializers
from .models import Participant, Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Participant
        fields = ['id', 'user', 'online', 'last_seen']

class MessageSerializer(serializers.ModelSerializer):
    sender = ParticipantSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'timestamp', 'read_by']
        read_only_fields = ['id', 'timestamp', 'sender']

class ConversationSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'name', 'participants', 'is_group', 'created_at', 'updated_at', 'last_message', 'unread_count']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        return MessageSerializer(last_message).data if last_message else None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            participant = request.user.participant
            return obj.messages.exclude(read_by=participant).count()
        return 0

class ConversationDetailSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'name', 'participants', 'is_group', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_messages(self, obj):
        messages = obj.messages.all().order_by('timestamp')
        return MessageSerializer(messages, many=True).data