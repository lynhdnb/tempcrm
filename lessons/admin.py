from django.contrib import admin
from .models import LessonType, Lesson, Attendance

@admin.register(LessonType)
class LessonTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color', 'duration_default', 'is_active')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('client', 'lesson_type', 'teacher', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'lesson_type', 'teacher', 'start_time')
    search_fields = ('client__last_name', 'client__first_name', 'teacher__user__last_name')
    date_hierarchy = 'start_time'
    raw_id_fields = ('client', 'teacher')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'is_present', 'recorded_at')
    list_filter = ('is_present',)
    search_fields = ('lesson__client__last_name',)