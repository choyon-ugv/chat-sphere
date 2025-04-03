from django.urls import path
from . import views

app_name = 'chat_bots'

urlpatterns = [
    path('participants/', views.ParticipantAPIView.as_view(), name='participant'),
    path('conversations/', views.ConversationAPIView.as_view(), name='conversation'),
    path('messages/<int:conversation_id>/', views.MessageAPIView.as_view(), name='message'),
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),
]