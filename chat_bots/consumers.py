import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Conversation, Message, Participant

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        # Accept connection first to avoid timeout
        await self.accept()

        # Then verify participation
        if await self.verify_participation():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.update_participant_status(online=True)
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.update_participant_status(online=False)

    @database_sync_to_async
    def verify_participation(self):
        # For general chat, allow all authenticated users
        if self.room_name == 'general':
            return True
            
        # For specific conversations, check participation
        return Conversation.objects.filter(
            id=self.room_name,
            participants__user=self.user
        ).exists()

    # ... rest of your consumer methods ...