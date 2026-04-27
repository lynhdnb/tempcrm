from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('accounts/login_redirect/', views.login_redirect, name='login_redirect'),
    path('accounts/logout/', views.logout_view, name='logout_view'),
]
