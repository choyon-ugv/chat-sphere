from django.urls import path
from . import views

app_name = 'chat_bots'

urlpatterns = [
    # API Endpoints
    path('participants/', views.ParticipantAPIView.as_view(), name='participant_api'),
    path('conversations/', views.ConversationAPIView.as_view(), name='conversation_api'),
    path('messages/<int:conversation_id>/', views.MessageAPIView.as_view(), name='message_api'),
    
    # Chat Room View
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),
]