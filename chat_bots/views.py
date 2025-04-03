from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.exceptions import NotFound, PermissionDenied
from django.contrib.auth import get_user_model
from .models import Participant, Conversation, Message
from .serializers import (
    ParticipantSerializer,
    ConversationSerializer,
    MessageSerializer,
    ConversationDetailSerializer
)

User = get_user_model()

class ParticipantAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            participant = request.user.participant
            serializer = ParticipantSerializer(participant)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Participant.DoesNotExist:
            return Response(
                {"detail": "Participant profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ConversationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        participant = request.user.participant
        conversations = participant.conversations.all().prefetch_related(
            'participants__user',
            'messages'
        ).order_by('-updated_at')
        
        serializer = ConversationSerializer(
            conversations, 
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        participant_ids = request.data.get('participant_ids', [])
        
        if not isinstance(participant_ids, list) or len(participant_ids) < 1:
            return Response(
                {"detail": "At least one participant is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure current user is included
        current_participant = request.user.participant
        if current_participant.id not in participant_ids:
            participant_ids.append(current_participant.id)

        serializer = ConversationSerializer(data=request.data)
        if serializer.is_valid():
            conversation = serializer.save(is_group=len(participant_ids) > 2)
            
            try:
                participants = Participant.objects.filter(id__in=participant_ids)
                conversation.participants.set(participants)
            except Participant.DoesNotExist:
                return Response(
                    {"detail": "One or more participants not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                ConversationDetailSerializer(conversation).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConversationDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, participant):
        try:
            return Conversation.objects.prefetch_related(
                'participants__user',
                'messages__sender__user'
            ).get(
                pk=pk,
                participants=participant
            )
        except Conversation.DoesNotExist:
            raise NotFound("Conversation not found or access denied")

    def get(self, request, pk):
        conversation = self.get_object(pk, request.user.participant)
        serializer = ConversationDetailSerializer(conversation)
        return Response(serializer.data)

    def delete(self, request, pk):
        conversation = self.get_object(pk, request.user.participant)
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MessageAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_conversation(self, pk, participant):
        try:
            return Conversation.objects.get(
                pk=pk,
                participants=participant
            )
        except Conversation.DoesNotExist:
            raise PermissionDenied("Conversation not found or access denied")

    def get(self, request, conversation_id):
        conversation = self.get_conversation(conversation_id, request.user.participant)
        messages = conversation.messages.select_related(
            'sender__user'
        ).order_by('timestamp')
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, conversation_id):
        conversation = self.get_conversation(conversation_id, request.user.participant)
        serializer = MessageSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                conversation=conversation,
                sender=request.user.participant
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
def chat_room(request, room_name):
    print(f"Accessed chat room: {room_name} with participant: {request.GET.get('participant')}")
    participant_name = request.GET.get('participant', 'User')
    return render(request, "chat/chat_room.html", {"room_name": room_name, "participant_name": participant_name})
