from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Participant, Conversation, Message
from .serializers import ParticipantSerializer, ConversationSerializer, MessageSerializer

class ParticipantAPIView(APIView):
    def post(self, request):
        name = request.data.get('name')
        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        participant, created = Participant.objects.get_or_create(name=name)
        serializer = ParticipantSerializer(participant)
        response = {
            'status' : 200,
            'success': True,
            'data': serializer.data
        }
        return Response(response, status=status.HTTP_201_CREATED)

class ConversationAPIView(APIView):
    def get(self, request):
        conversations = Conversation.objects.all().prefetch_related('participants', 'messages')
        serializer = ConversationSerializer(conversations, many=True)
        response = {
            'status' : 200,
            'success': True,
            'data': serializer.data,
        }
        return Response(response, status=status.HTTP_201_CREATED)

    def post(self, request):
        serializer = ConversationSerializer(data=request.data)
        if serializer.is_valid():
            conversation = serializer.save()
            return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MessageAPIView(APIView):
    def get(self, request, conversation_id):
        messages = Message.objects.filter(conversation_id=conversation_id).select_related('sender')
        serializer = MessageSerializer(messages, many=True)
        response = {
            'status' : 200,
            'success': True,
            'data': serializer.data,
        }
        return Response(response)

    def post(self, request, conversation_id):
        sender_name = request.data.get('sender')
        content = request.data.get('content')
        
        if not sender_name or not content:
            return Response(
                {'error': 'Both sender and content are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            sender = Participant.objects.get(name=sender_name)
            conversation = Conversation.objects.get(id=conversation_id)
            
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=content
            )
            
            return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
        except (Participant.DoesNotExist, Conversation.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)