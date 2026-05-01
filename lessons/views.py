from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import Lesson
from .serializers import LessonSerializer

# Стандартные представления (если нужны)
def index(request):
    return render(request, 'lessons/index.html')

# API для FullCalendar
class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lesson.objects.filter(start_time__gte=timezone.now())
    serializer_class = LessonSerializer

# Представление для страницы календаря
def calendar_view(request):
    return render(request, 'calendar.html')