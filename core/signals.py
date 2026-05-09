from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta

from .models import Client, Role, RoleAssignment, EmployeeProfile
from interactions.models import Interaction


@receiver(post_save, sender=Client)
def update_client_silent_days(sender, instance, **kwargs):
    """Автоматическое обновление дней без активности при сохранении клиента"""
    if instance.last_interaction_date:
        instance.silent_days = (timezone.now().date() - instance.last_interaction_date).days
        # Сохраняем без рекурсии
        Client.objects.filter(pk=instance.pk).update(
            silent_days=instance.silent_days
        )


@receiver(post_save, sender=Interaction)
def update_client_last_interaction(sender, instance, **kwargs):
    """Обновление даты последнего взаимодействия при создании Interaction"""
    if instance.client and instance.date_time:
        client = instance.client
        interaction_date = instance.date_time.date()
        
        # Обновляем только если новая дата больше текущей
        if not client.last_interaction_date or interaction_date > client.last_interaction_date:
            Client.objects.filter(pk=client.pk).update(
                last_interaction_date=interaction_date
            )
            
            # Автоматическое обновление статуса
            client.refresh_from_db()
            client.update_status()


@receiver(post_save, sender=RoleAssignment)
def set_primary_role_on_employee(sender, instance, created, **kwargs):
    """Автоматическое назначение основной роли в EmployeeProfile"""
    if created and instance.is_primary:
        try:
            profile = EmployeeProfile.objects.get(user=instance.user)
            profile.primary_role = instance.role
            profile.save(update_fields=['primary_role'])
        except EmployeeProfile.DoesNotExist:
            # Профиль будет создан отдельно
            pass


@receiver(post_save, sender=User)
def create_employee_profile_on_user_create(sender, instance, created, **kwargs):
    """Создание EmployeeProfile при создании нового пользователя-сотрудника"""
    if created:
        # Проверяем, есть ли у пользователя роль сотрудника
        if instance.role_assignments.exists():
            RoleAssignment.objects.filter(user=instance, is_primary=True).first()
            # Профиль будет создан вручную или через админку


@receiver(post_save, sender=Client)
def check_client_status_automatically(sender, instance, **kwargs):
    """Проверка и обновление статуса клиента при сохранении"""
    if instance.last_interaction_date:
        instance.update_status()


# Периодическая задача для обновления статусов всех клиентов
# Это должно вызываться через Celery или django-celery-beat
def update_all_client_statuses():
    """Массовое обновление статусов всех активных клиентов"""
    today = timezone.now().date()
    clients = Client.objects.filter(is_active=True).exclude(status='CANCELLED')
    
    updated_count = 0
    for client in clients:
        if client.last_interaction_date:
            silent_days = (today - client.last_interaction_date).days
            
            old_status = client.status
            new_status = client.status
            
            if silent_days > 30:
                new_status = 'LOST'
            elif silent_days > 14:
                new_status = 'SILENT'
            elif silent_days <= 14 and client.status in ['SILENT', 'LOST']:
                new_status = 'ACTIVE'
            
            if old_status != new_status:
                Client.objects.filter(pk=client.pk).update(
                    status=new_status,
                    silent_days=silent_days
                )
                updated_count += 1
    
    return updated_count
