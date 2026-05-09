from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse


def user_has_role(user, role_code):
    """
    Проверка наличия у пользователя роли
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    return user.role_assignments.filter(
        role__code=role_code,
        role__is_active=True
    ).exists()


def user_has_permission(user, permission_field):
    """
    Проверка наличия у пользователя конкретного права
    permission_field - имя поля в Role, например 'can_view_finance'
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    # Получаем основную роль пользователя
    primary_assignment = user.role_assignments.filter(
        is_primary=True,
        role__is_active=True
    ).select_related('role').first()
    
    if primary_assignment:
        return getattr(primary_assignment.role, permission_field, False)
    
    # Если нет основной роли, проверяем все активные роли
    return user.role_assignments.filter(
        role__is_active=True
    ).filter(**{permission_field: True}).exists()


def role_required(*role_codes):
    """
    Декоратор для проверки наличия хотя бы одной из указанных ролей
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'{settings.LOGIN_URL}?next={request.path}')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            has_role = any(
                user_has_role(request.user, role) 
                for role in role_codes
            )
            
            if not has_role:
                raise PermissionDenied
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def permission_required(permission_field):
    """
    Декоратор для проверки наличия конкретного права
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'{settings.LOGIN_URL}?next={request.path}')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if not user_has_permission(request.user, permission_field):
                raise PermissionDenied
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def manager_required(view_func):
    """
    Декоратор для доступа менеджеров и выше
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        allowed_roles = ['OWNER', 'ADMIN', 'MANAGER']
        has_role = any(
            user_has_role(request.user, role) 
            for role in allowed_roles
        )
        
        if not has_role:
            raise PermissionDenied
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def teacher_required(view_func):
    """
    Декоратор для доступа преподавателей и выше
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        allowed_roles = ['OWNER', 'ADMIN', 'MANAGER', 'TEACHER']
        has_role = any(
            user_has_role(request.user, role) 
            for role in allowed_roles
        )
        
        if not has_role:
            raise PermissionDenied
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def finance_access_required(view_func):
    """
    Декоратор для доступа к финансовым данным
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if not user_has_permission(request.user, 'can_view_finance'):
            raise PermissionDenied
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def edit_finance_required(view_func):
    """
    Декоратор для редактирования финансовых данных
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if not user_has_permission(request.user, 'can_edit_finance'):
            raise PermissionDenied
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# Хелперы для шаблонов
def get_user_display_role(user):
    """
    Получить отображаемое имя основной роли пользователя
    """
    if not user.is_authenticated:
        return 'Гость'
    
    if user.is_superuser:
        return 'Суперпользователь'
    
    primary_assignment = user.role_assignments.filter(
        is_primary=True
    ).select_related('role').first()
    
    if primary_assignment:
        return primary_assignment.role.name
    
    return 'Без роли'


def get_user_roles(user):
    """
    Получить все роли пользователя для отображения
    """
    if not user.is_authenticated:
        return []
    
    return user.role_assignments.filter(
        role__is_active=True
    ).select_related('role')
