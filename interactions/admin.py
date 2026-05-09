from django.contrib import admin
from .models import InteractionType, Interaction, Comment, Notification

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

    fieldsets = (
        ('Основная информация', {
            'fields': ('client', 'interaction_type', 'subject')
        }),
        ('Детали', {
            'fields': ('date_time', 'duration_minutes', 'note', 'status')
        }),
        ('Напоминание', {
            'fields': ('is_reminder', 'reminder_time'),
            'classes': ('collapse',)
        }),
        ('Создал', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('interaction', 'user', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('text', 'user__username')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('client', 'notification_type', 'send_method', 'status', 'scheduled_for', 'created_at')
    list_filter = ('notification_type', 'send_method', 'status', 'scheduled_for')
    search_fields = ('client__last_name', 'client__first_name', 'title', 'message')
    readonly_fields = ('created_at', 'sent_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('client', 'lesson', 'enrollment', 'notification_type')
        }),
        ('Контент', {
            'fields': ('title', 'message')
        }),
        ('Отправка', {
            'fields': ('send_method', 'status', 'scheduled_for', 'sent_at')
        }),
        ('Даты', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )