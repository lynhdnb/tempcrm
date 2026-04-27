from django.urls import path
from . import views

urlpatterns = [
    path('', views.lesson_list, name='lesson_list'),
    path('new/', views.lesson_create, name='lesson_create'),
    path('<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('<int:pk>/edit/', views.lesson_update, name='lesson_update'),
    path('<int:pk>/delete/', views.lesson_delete, name='lesson_delete'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/events/', views.lesson_events_api, name='lesson_events_api'),
]