from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from lessons.views import LessonViewSet, calendar_view

router = DefaultRouter()
router.register(r'api/lessons', LessonViewSet, basename='lesson-api')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('calendar/', calendar_view, name='calendar'),
    path('', include(router.urls)),
]