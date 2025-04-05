from django.urls import path
from .views import ParticipantAPIView, ConversationAPIView, MessageAPIView, chat_room

app_name = 'chat_bots'

urlpatterns = [
    path('participants/', ParticipantAPIView.as_view(), name='participant'),
    path('conversations/', ConversationAPIView.as_view(), name='conversation'),
    path('messages/<int:conversation_id>/', MessageAPIView.as_view(), name='message'),
    path('chat/<str:room_name>/', chat_room, name='chat_room'),
]