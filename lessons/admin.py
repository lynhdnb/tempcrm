from django.contrib import admin
from .models import Room, Lesson

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['client', 'get_teacher', 'room', 'start_time', 'end_time']
    list_filter = ['teacher', 'room', 'start_time']
    search_fields = ['client__last_name', 'client__first_name']
    date_hierarchy = 'start_time'
    autocomplete_fields = ['client', 'teacher', 'room']
    
    def get_teacher(self, obj):
        if obj.teacher:
            return obj.teacher.user.get_full_name() or obj.teacher.user.username
        return "Самостоятельная практика"
    get_teacher.short_description = 'Преподаватель'