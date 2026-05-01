from django.contrib import admin
from .models import InteractionType, Interaction, Comment

@admin.register(InteractionType)
class InteractionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color')
    search_fields = ('name',)

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('client', 'interaction_type', 'subject', 'date_time', 'status', 'is_reminder', 'created_by')
    list_filter = ('status', 'is_reminder', 'interaction_type', 'date_time')
    search_fields = ('client__last_name', 'subject', 'note')
    raw_id_fields = ('client', 'created_by')
    date_hierarchy = 'date_time'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('interaction', 'user', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('text', 'user__username')