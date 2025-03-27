from django.urls import path
from .views import ParticipantAPIView, ConversationAPIView, MessageAPIView

urlpatterns = [
    path('participants/', ParticipantAPIView.as_view(), name='participants'),
    path('conversations/', ConversationAPIView.as_view(), name='conversations'),
    path('conversations/<int:conversation_id>/messages/', MessageAPIView.as_view(), name='messages'),
]