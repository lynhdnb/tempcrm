from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cabinet/', include('client_cabinet.urls')),
    path('impersonate/<int:user_id>/', core_views.impersonate_user, name='impersonate_user'),
    path('stop-impersonation/', core_views.stop_impersonation, name='stop_impersonation'),
    path('sales/', include('sales.urls')),
    
    # Кастомные login/logout
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', core_views.logout_view, name='logout'),
    path('accounts/login_redirect/', core_views.login_redirect, name='login_redirect'),
    
    path('', include('core.urls')),
    path('clients/', include('clients.urls')),
    path('lessons/', include('lessons.urls')),
]