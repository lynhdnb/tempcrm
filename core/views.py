from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


# ========================================
# DASHBOARD
# ========================================
@login_required
def dashboard(request):
    """
    Умный дашборд — распределяет пользователей по ролям
    """
    user = request.user
    
    # Проверяем наличие UserProfile с ролью (для преподавателей, менеджеров и др.)
    try:
        role = getattr(user.profile, 'role', None)
        
        if role == 'manager':
            return redirect('sales:manager_dashboard')
        elif role == 'owner':
            return render(request, 'core/dashboard_owner.html')
        elif role == 'admin':
            return render(request, 'core/dashboard_admin.html')
        elif role == 'teacher':
            return render(request, 'core/dashboard_teacher.html')
    except Exception:
        pass
    
    # Сотрудники/Админы без UserProfile — в админку
    if user.is_staff or user.is_superuser:
        return redirect('/admin/')
    
    # Клиенты — в ЛК
    return redirect('client_cabinet:dashboard')


# ========================================
# ERROR HANDLERS
# ========================================
def handler403(request, exception=None):
    return render(request, '403.html', status=403)


# ========================================
# PROFILE
# ========================================
class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Телефон успешно обновлён.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'core/profile.html', {
        'form': form,
        'user': request.user,
        'profile': profile
    })


# ========================================
# IMPERSONATION
# ========================================
def impersonate_user(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, "Доступ запрещён")
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    request.session['impersonated_user_id'] = user.id
    messages.success(request, f"Вы вошли как {user.get_full_name or user.username}")
    return redirect('dashboard')

def stop_impersonation(request):
    if 'impersonated_user_id' in request.session:
        del request.session['impersonated_user_id']
        messages.success(request, "Имперсонация завершена")
    return redirect('dashboard')


# ========================================
# LOGIN/LOGOUT REDIRECTS
# ========================================
@login_required
def login_redirect(request):
    """
    Умный редирект после входа:
    - Клиенты → /cabinet/dashboard/
    - Сотрудники (is_staff, is_superuser, role=teacher/manager/admin/owner) → /
    """
    user = request.user
    
    # Проверяем, является ли пользователь сотрудником ИЛИ имеет UserProfile с ролью
    is_employee = user.is_staff or user.is_superuser
    
    # Дополнительно проверяем наличие UserProfile с ролью (для преподавателей и др.)
    if not is_employee:
        try:
            role = getattr(user.profile, 'role', None)
            if role in ['teacher', 'manager', 'admin', 'owner']:
                is_employee = True
        except Exception:
            pass
    
    if is_employee:
        return redirect('/')
    
    # Проверяем, является ли пользователь клиентом (через ClientCabinetProfile)
    try:
        from client_cabinet.models import ClientCabinetProfile
        profile = ClientCabinetProfile.objects.filter(user=user).first()
        if profile and profile.client:
            return redirect('client_cabinet:dashboard')
    except Exception:
        pass
    
    # По умолчанию — админка (для пользователей без профиля)
    return redirect('/admin/')


def logout_view(request):
    """
    Выход из системы — показывает страницу logged_out.html
    """
    auth_logout(request)
    
    # Рендерим шаблон напрямую (без редиректа)
    return render(request, 'registration/logged_out.html')