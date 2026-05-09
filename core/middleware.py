from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.conf import settings


class PermissionMiddleware:
    """
    Middleware для проверки прав доступа к URL
    """
    
    # Маппинг URL паттернов на требуемые права
    PERMISSION_MAP = {
        '/admin/': ['OWNER', 'ADMIN'],
        '/finance/': ['OWNER', 'ADMIN', 'MANAGER'],
        '/payments/': ['OWNER', 'ADMIN', 'MANAGER'],
        '/reports/': ['OWNER', 'ADMIN', 'MANAGER'],
        '/settings/': ['OWNER', 'ADMIN'],
        '/lessons/': ['OWNER', 'ADMIN', 'MANAGER', 'TEACHER'],
        '/tasks/': ['OWNER', 'ADMIN', 'MANAGER', 'TEACHER'],
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Пропускаем проверку для статических файлов и media
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        # Пропускаем проверку если пользователь не аутентифицирован
        # (это будет обработано декораторами в views)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Проверка прав для защищенных URL
        if request.user.is_superuser:
            return self.get_response(request)
        
        # Проверяем соответствие URL требуемым ролям
        for path_prefix, required_roles in self.PERMISSION_MAP.items():
            if request.path.startswith(path_prefix):
                has_role = any(
                    self._user_has_role(request.user, role)
                    for role in required_roles
                )
                
                if not has_role:
                    # Возвращаем 403 или редирект
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return HttpResponseForbidden('Доступ запрещен')
                    return redirect('/dashboard/')
        
        return self.get_response(request)
    
    def _user_has_role(self, user, role_code):
        """Проверка наличия роли у пользователя"""
        return user.role_assignments.filter(
            role__code=role_code,
            role__is_active=True
        ).exists()


class RoleBasedMenuMiddleware:
    """
    Middleware для добавления информации о ролях в контекст шаблона
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_template_response(self, request, response):
        """Добавляем информацию о ролях в контекст"""
        if hasattr(response, 'context_data'):
            if not response.context_data:
                response.context_data = {}
            
            response.context_data['user_roles'] = self._get_user_roles(request.user)
            response.context_data['user_can_view_finance'] = self._has_permission(
                request.user, 'can_view_finance'
            )
            response.context_data['user_can_edit_finance'] = self._has_permission(
                request.user, 'can_edit_finance'
            )
            response.context_data['user_can_manage_users'] = self._has_permission(
                request.user, 'can_manage_users'
            )
            response.context_data['user_can_manage_settings'] = self._has_permission(
                request.user, 'can_manage_settings'
            )
        
        return response
    
    def _get_user_roles(self, user):
        """Получить все роли пользователя"""
        if not user.is_authenticated:
            return []
        
        if user.is_superuser:
            return [{'code': 'SUPERUSER', 'name': 'Суперпользователь', 'is_primary': True}]
        
        roles = []
        assignments = user.role_assignments.filter(role__is_active=True).select_related('role')
        
        for assignment in assignments:
            roles.append({
                'code': assignment.role.code,
                'name': assignment.role.name,
                'is_primary': assignment.is_primary,
                'can_view_clients': assignment.role.can_view_clients,
                'can_edit_clients': assignment.role.can_edit_clients,
                'can_view_finance': assignment.role.can_view_finance,
                'can_edit_finance': assignment.role.can_edit_finance,
                'can_view_schedule': assignment.role.can_view_schedule,
                'can_edit_schedule': assignment.role.can_edit_schedule,
                'can_view_tasks': assignment.role.can_view_tasks,
                'can_create_tasks': assignment.role.can_create_tasks,
                'can_manage_users': assignment.role.can_manage_users,
                'can_view_reports': assignment.role.can_view_reports,
                'can_manage_settings': assignment.role.can_manage_settings,
            })
        
        return roles
    
    def _has_permission(self, user, permission_field):
        """Проверка наличия права у пользователя"""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        primary_assignment = user.role_assignments.filter(
            is_primary=True,
            role__is_active=True
        ).select_related('role').first()
        
        if primary_assignment:
            return getattr(primary_assignment.role, permission_field, False)
        
        return False
