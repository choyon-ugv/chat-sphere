from django.contrib import admin
from unfold.admin import ModelAdmin
from django.forms import Textarea
from django.utils.timezone import now
from .models import Participant, Conversation, Message


@admin.register(Participant)
class CustomAdminClass(admin.ModelAdmin):
    list_display = ('id', 'name', 'online', 'last_seen', 'status')  
    search_fields = ('name',)  
    list_filter = ('online', 'last_seen')  
    readonly_fields = ('last_seen',)  
    ordering = ('-last_seen',)  

    fieldsets = (
        ('User Information', {
            'fields': ('name', 'online')
        }),
        ('Activity', {
            'fields': ('last_seen',)
        }),
    )

    def status(self, obj):
        time_difference = now() - obj.last_seen
        return "Online" if obj.online else f"Last seen {time_difference.seconds // 60} min ago"
    status.short_description = "Status"


@admin.register(Conversation)
class CustomAdminClass(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_group', 'created_at', 'updated_at', 'participant_count')  
    search_fields = ('name', 'participants__name')  
    list_filter = ('is_group', 'created_at')  
    readonly_fields = ('created_at', 'updated_at')  
    filter_horizontal = ('participants',)  

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_group', 'participants')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = "Participants"
    
    
    
@admin.register(Message)
class CustomAdminClass(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'content_preview', 'timestamp')  # Show these fields in the list view
    search_fields = ('sender__name', 'content')  # Enable searching by sender name and content
    list_filter = ('timestamp', 'conversation')  # Filter messages by conversation and timestamp
    readonly_fields = ('timestamp',)  # Make timestamp read-only
    filter_horizontal = ('read_by',)  # Improve the ManyToManyField display

    fieldsets = (
        ('Message Info', {
            'fields': ('conversation', 'sender', 'content', 'timestamp', 'read_by')
        }),
    )

    formfield_overrides = {
        Message._meta.get_field('content'): {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
    }

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "Content Preview"  # Custom column name