import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import Conversation, Message, Participant

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.user = None
        self.participant = None
        self.participant_name = None

    async def connect(self):
        try:
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_name}'
            
            # Extract participant name from query string
            query_string = self.scope.get('query_string', b'').decode()
            params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            self.participant_name = params.get('participant', '')

            if not self.participant_name:
                await self.close(code=4003)
                return

            # Get participant from database
            self.participant = await self.get_participant_by_name(self.participant_name)
            if not self.participant:
                await self.close(code=4004)
                return

            self.user = self.participant.user

            await self.accept()

            conversation = await self.get_or_create_conversation()
            if not conversation:
                await self.close(code=4005)
                return

            await self.add_participant_to_conversation(conversation)
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.update_participant_status(online=True)

            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'system',
                'message': f"Connected to '{self.room_name}' as {self.user.username}",
                'timestamp': self.format_timestamp(timezone.now())
            }))

            # Notify others about new participant
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'system_message',
                    'message': f"{self.user.username} joined the chat",
                    'timestamp': self.format_timestamp(timezone.now()),
                    'exclude': self.channel_name
                }
            )

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self.close(code=4006)

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'participant'):
                await self.update_participant_status(online=False)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'system_message',
                        'message': f"{self.user.username} left the chat",
                        'timestamp': self.format_timestamp(timezone.now()),
                        'exclude': self.channel_name
                    }
                )
            
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
        except Exception as e:
            logger.error(f"Disconnection error: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': self.format_timestamp(timezone.now())
                }))
            elif 'message' in data:
                message_content = data['message'].strip()
                if message_content:
                    message = await self.save_message(message_content)
                    if message:
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'chat_message',
                                'message': message.content,
                                'sender': self.user.username,
                                'sender_id': str(self.participant.id),
                                'timestamp': self.format_timestamp(message.timestamp),
                                'message_id': str(message.id),
                                'exclude': self.channel_name
                            }
                        )
        except json.JSONDecodeError:
            logger.error("Received invalid JSON data")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    async def chat_message(self, event):
        if event.get('exclude') == self.channel_name:
            return
            
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    async def system_message(self, event):
        if event.get('exclude') == self.channel_name:
            return
            
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': event['message'],
        }))

    def format_timestamp(self, timestamp):
        return timestamp.strftime('%I:%M %p')

    @database_sync_to_async
    def get_participant_by_name(self, name):
        try:
            return Participant.objects.select_related('user').get(user__username=name)
        except Participant.DoesNotExist:
            logger.error(f"Participant not found: {name}")
            return None

    @database_sync_to_async
    def get_or_create_conversation(self):
        try:
            if self.room_name == 'general':
                conversation, created = Conversation.objects.get_or_create(
                    special_identifier='general',
                    defaults={
                        'name': 'General Chat',
                        'is_group': True
                    }
                )
                if created:
                    logger.info("Created general chat room")
                return conversation
            return Conversation.objects.get(id=self.room_name)
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return None

    @database_sync_to_async
    def add_participant_to_conversation(self, conversation):
        try:
            if self.participant not in conversation.participants.all():
                conversation.participants.add(self.participant)
                logger.info(f"Added {self.user.username} to {conversation.name}")
        except Exception as e:
            logger.error(f"Error adding participant to conversation: {str(e)}")

    @database_sync_to_async
    def save_message(self, content):
        try:
            if self.room_name == 'general':
                conversation = Conversation.objects.get(special_identifier='general')
            else:
                conversation = Conversation.objects.get(id=self.room_name)
            
            message = Message.objects.create(
                conversation=conversation,
                sender=self.participant,
                content=content
            )
            logger.info(f"Message saved by {self.user.username}: {message.id}")
            return message
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            return None

    @database_sync_to_async
    def update_participant_status(self, online):
        try:
            self.participant.online = online
            self.participant.last_seen = timezone.now()
            self.participant.save()
            logger.info(f"Updated {self.user.username} status to {'online' if online else 'offline'}")
        except Exception as e:
            logger.error(f"Error updating participant status: {str(e)}")