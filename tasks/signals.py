from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Task


@receiver(pre_save, sender=Task)
def auto_set_created_by(sender, instance, **kwargs):
    """
    Автоматическая установка постановщика задачи
    Если не указано, используем текущего пользователя из контекста
    (требуется middleware для передачи user в request)
    """
    if not instance.created_by and not instance.pk:
        # TODO: Получить из thread-local или request
        # Для простоты пока пропускаем
        pass


@receiver(post_save, sender=Task)
def auto_set_completed_at_on_done(sender, instance, created, **kwargs):
    """
    Автоматическая установка даты выполнения при смене статуса на DONE
    """
    if instance.status == 'DONE' and not instance.completed_at:
        Task.objects.filter(pk=instance.pk).update(
            completed_at=timezone.now()
        )


@receiver(pre_save, sender=Task)
def validate_task_dates(sender, instance, **kwargs):
    """
    Валидация дат задачи
    """
    # Преобразуем в объект date, если это строка
    due_date = instance.due_date
    if isinstance(due_date, str):
        from datetime import datetime
        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return  # Если не удалось преобразовать, пропускаем
    
    if due_date and due_date < timezone.now().date():
        # Можно поднять предупреждение, но не блокировать
        pass


@receiver(post_save, sender=Task)
def notify_about_task_assignment(sender, instance, created, **kwargs):
    """
    Уведомление о назначении задачи
    """
    if created and instance.assigned_to:
        # TODO: Отправить уведомление исполнителю
        # email, push, etc.
        pass


@receiver(post_save, sender=Task)
def notify_about_overdue_task(sender, instance, **kwargs):
    """
    Уведомление о просроченной задаче
    Должно запускаться ежедневно через Celery beat
    """
    if instance.due_date and instance.status != 'DONE':
        from datetime import timedelta
        days_overdue = (timezone.now().date() - instance.due_date).days
        
        if days_overdue > 0 and days_overdue <= 1:
            # Только что просрочена - отправить напоминание
            # TODO: Отправить уведомление
            pass


# Автоматическая проверка просроченных задач
def check_overdue_tasks():
    """
    Функция для проверки просроченных задач
    Должна вызываться через Celery beat ежедневно
    """
    from django.utils import timezone
    
    today = timezone.now().date()
    overdue_tasks = Task.objects.filter(
        status__in=['TODO', 'IN_PROGRESS', 'REVIEW'],
        due_date__lt=today
    )
    
    updated_count = 0
    for task in overdue_tasks:
        # Можно отправить напоминание исполнителю
        # Можно обновить приоритет на URGENT
        updated_count += 1
    
    return updated_count
