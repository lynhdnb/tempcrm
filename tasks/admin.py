from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_to', 'client', 'priority', 'status', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'due_date', 'assigned_to')
    search_fields = ('title', 'description', 'client__last_name', 'assigned_to__username')
    date_hierarchy = 'due_date'
    raw_id_fields = ('assigned_to', 'created_by', 'client')
    
    fieldsets = (
        (None, {'fields': ('title', 'description')}),
        ('Назначение', {'fields': ('client', 'assigned_to')}),
        ('Статус и приоритет', {'fields': ('priority', 'status', 'due_date')}),
    )