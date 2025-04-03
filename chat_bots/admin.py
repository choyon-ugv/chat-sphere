from django.contrib import admin
from .models import Participant, Conversation, Message

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'online_status', 'last_seen')
    list_filter = ('online', 'last_seen')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('last_seen',)
    
    def online_status(self, obj):
        return "Online" if obj.online else "Offline"
    online_status.short_description = 'Status'
    
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'display_name', 'participant_count', 'is_group', 'created_date')
    list_filter = ('is_group', 'created_at')
    filter_horizontal = ('participants',)
    search_fields = ('name', 'participants__user__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def display_name(self, obj):
        return obj.name if obj.name else "No name"
    display_name.short_description = 'Name'
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'
    
    def created_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d')
    created_date.short_description = 'Created'
    created_date.admin_order_field = 'created_at'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('truncated_content', 'conversation_id', 'sender_name', 'message_time')
    list_filter = ('conversation', 'timestamp')
    search_fields = ('content', 'sender__user__username')
    readonly_fields = ('timestamp',)
    
    def truncated_content(self, obj):
        return f"{obj.content[:50]}..." if len(obj.content) > 50 else obj.content
    truncated_content.short_description = 'Content'
    
    def sender_name(self, obj):
        return obj.sender.user.username
    sender_name.short_description = 'Sender'
    sender_name.admin_order_field = 'sender__user__username'
    
    def conversation_id(self, obj):
        return obj.conversation.id
    conversation_id.short_description = 'Conversation ID'
    conversation_id.admin_order_field = 'conversation__id'
    
    def message_time(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M')
    message_time.short_description = 'Time'
    message_time.admin_order_field = 'timestamp'