# chat/consumers.py
import json
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Participant, Conversation, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.participant_name = self.scope['query_string'].decode().split('participant=')[-1] or 'Anonymous'

        await self.update_participant_status(online=True)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"WebSocket connected to room: {self.room_name} by {self.participant_name}")

    async def disconnect(self, close_code):
        await self.update_participant_status(online=False)
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"WebSocket disconnected from room: {self.room_name} by {self.participant_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_name = data.get('sender', self.participant_name)

        message_obj = await self.save_message(sender_name, message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender_name,
                'timestamp': message_obj.timestamp.isoformat() if message_obj else None
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def update_participant_status(self, online):
        participant, _ = Participant.objects.get_or_create(name=self.participant_name)
        participant.online = online
        participant.last_seen = timezone.now()
        participant.save()

    @database_sync_to_async
    def save_message(self, sender_name, content):
        try:
            sender = Participant.objects.get(name=sender_name)
            conversation = Conversation.objects.get(id=self.room_name)
            return Message.objects.create(conversation=conversation, sender=sender, content=content)
        except (Participant.DoesNotExist, Conversation.DoesNotExist) as e:
            print(f"Error saving message: {e}")
            return None