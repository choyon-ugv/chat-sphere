from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Participant, Conversation, Message
from .serializers import ParticipantSerializer, ConversationSerializer, MessageSerializer
from django.contrib.auth.models import User  # For authentication (optional)

class ParticipantAPIView(APIView):
    def post(self, request):
        name = request.data.get('name')
        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        participant, created = Participant.objects.get_or_create(name=name)
        serializer = ParticipantSerializer(participant)
        return Response({
            'status': 200,
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ConversationAPIView(APIView):
    def get(self, request):
        conversations = Conversation.objects.all().prefetch_related('participants', 'messages')
        serializer = ConversationSerializer(conversations, many=True)
        return Response({
            'status': 200,
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        participant_ids = request.data.get('participant_ids', [])
        if len(participant_ids) < 2:
            return Response({'error': 'At least two participants are required'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ConversationSerializer(data=request.data)
        if serializer.is_valid():
            conversation = serializer.save()
            participants = Participant.objects.filter(id__in=participant_ids)
            conversation.participants.set(participants)
            # Set is_one_to_one or is_group based on participant count
            conversation.is_one_to_one = len(participant_ids) == 2
            conversation.is_group = len(participant_ids) > 2
            conversation.save()
            return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MessageAPIView(APIView):
    def get(self, request, conversation_id):
        messages = Message.objects.filter(conversation_id=conversation_id).select_related('sender')
        serializer = MessageSerializer(messages, many=True)
        return Response({
            'status': 200,
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request, conversation_id):
        sender_name = request.data.get('sender')
        content = request.data.get('content')
        
        if not sender_name or not content:
            return Response({'error': 'Both sender and content are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sender = Participant.objects.get(name=sender_name)
            conversation = Conversation.objects.get(id=conversation_id)
            message = Message.objects.create(conversation=conversation, sender=sender, content=content)
            return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
        except (Participant.DoesNotExist, Conversation.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

# chat/views.py
def chat_room(request, room_name):
    print(f"Accessed chat room: {room_name} with participant: {request.GET.get('participant')}")
    participant_name = request.GET.get('participant', 'User')
    return render(request, "chat/chat_room.html", {"room_name": room_name, "participant_name": participant_name})