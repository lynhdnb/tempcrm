from django.urls import path
from . import views

urlpatterns = [
    path('', views.client_list, name='client_list'),
    path('new/', views.client_create, name='client_create'),
    path('<int:client_id>/edit/', views.client_edit, name='client_edit'),
    path('<int:client_id>/interaction/add/', views.add_interaction, name='add_interaction'),
    path('<int:client_id>/note/add/', views.add_note, name='add_note'),
    path('<int:client_id>/task/add/', views.add_task, name='add_task'),
    path('task/<int:interaction_id>/edit/', views.edit_task, name='edit_task'),
    path('task/<int:interaction_id>/complete/', views.mark_task_completed, name='mark_task_completed'),
    path('note/<int:interaction_id>/edit/', views.edit_note, name='edit_note'),
    path('<int:client_id>/', views.client_detail, name='client_detail'),
]