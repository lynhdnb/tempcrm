from django.core.management.base import BaseCommand
from core.models import Role


class Command(BaseCommand):
    help = 'Создание базовых ролей для системы'

    def handle(self, *args, **kwargs):
        # Определение ролей и их прав
        roles_data = [
            {
                'code': 'OWNER',
                'name': 'Владелец',
                'description': 'Полный доступ ко всей системе',
                'permissions': {
                    'can_view_clients': True,
                    'can_edit_clients': True,
                    'can_view_finance': True,
                    'can_edit_finance': True,
                    'can_view_schedule': True,
                    'can_edit_schedule': True,
                    'can_view_tasks': True,
                    'can_create_tasks': True,
                    'can_manage_users': True,
                    'can_view_reports': True,
                    'can_manage_settings': True,
                }
            },
            {
                'code': 'ADMIN',
                'name': 'Администратор',
                'description': 'Управление пользователями и настройками',
                'permissions': {
                    'can_view_clients': True,
                    'can_edit_clients': True,
                    'can_view_finance': True,
                    'can_edit_finance': True,
                    'can_view_schedule': True,
                    'can_edit_schedule': True,
                    'can_view_tasks': True,
                    'can_create_tasks': True,
                    'can_manage_users': True,
                    'can_view_reports': True,
                    'can_manage_settings': True,
                }
            },
            {
                'code': 'MANAGER',
                'name': 'Менеджер',
                'description': 'Работа с клиентами, расписанием и платежами',
                'permissions': {
                    'can_view_clients': True,
                    'can_edit_clients': True,
                    'can_view_finance': True,
                    'can_edit_finance': True,
                    'can_view_schedule': True,
                    'can_edit_schedule': True,
                    'can_view_tasks': True,
                    'can_create_tasks': True,
                    'can_manage_users': False,
                    'can_view_reports': True,
                    'can_manage_settings': False,
                }
            },
            {
                'code': 'TEACHER',
                'name': 'Преподаватель',
                'description': 'Управление своими занятиями и учениками',
                'permissions': {
                    'can_view_clients': True,
                    'can_edit_clients': False,
                    'can_view_finance': False,
                    'can_edit_finance': False,
                    'can_view_schedule': True,
                    'can_edit_schedule': False,
                    'can_view_tasks': True,
                    'can_create_tasks': True,
                    'can_manage_users': False,
                    'can_view_reports': False,
                    'can_manage_settings': False,
                }
            },
            {
                'code': 'STUDENT',
                'name': 'Ученик',
                'description': 'Личный кабинет ученика',
                'permissions': {
                    'can_view_clients': False,
                    'can_edit_clients': False,
                    'can_view_finance': False,
                    'can_edit_finance': False,
                    'can_view_schedule': True,
                    'can_edit_schedule': False,
                    'can_view_tasks': False,
                    'can_create_tasks': False,
                    'can_manage_users': False,
                    'can_view_reports': False,
                    'can_manage_settings': False,
                }
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'is_active': True,
                    **role_data['permissions']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    f'[OK] Создана роль: {role.name} ({role.code})'
                )
            else:
                # Обновляем права существующей роли
                for key, value in role_data['permissions'].items():
                    setattr(role, key, value)
                role.save()
                updated_count += 1
                self.stdout.write(
                    f'[UPDATE] Обновлена роль: {role.name} ({role.code})'
                )
        
        self.stdout.write(f'\nГотово! Создано: {created_count}, Обновлено: {updated_count}')
        
        # Вывод всех ролей
        self.stdout.write('\nВсе роли в системе:')
        for role in Role.objects.all():
            status = 'Активна' if role.is_active else 'Неактивна'
            self.stdout.write(f'  - {role.name} ({role.code}): {status}')
