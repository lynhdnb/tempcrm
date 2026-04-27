from django.urls import path
from . import views

app_name = 'client_cabinet'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('confirm-email/', views.confirm_email, name='confirm_email'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('schedule/', views.schedule, name='schedule'),
    path('courses/', views.courses, name='courses'),
    path('installments/', views.installments, name='installments'),
    path('profile/', views.profile_edit, name='profile_edit'),
    path('password-change/', views.password_change, name='password_change'),
#    path('progress/', views.progress, name='progress'),
#    path('purchases/', views.purchases, name='purchases'),
#    path('payments/', views.payments, name='payments'),
    path('confirm-email/<str:token>/', views.confirm_email_token, name='confirm_email_token'),
]
