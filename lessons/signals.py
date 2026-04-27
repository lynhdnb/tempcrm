from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from django.utils import timezone
from .models import Lesson
from clients.models import Interaction
from core.models import UserProfile

@receiver(post_save, sender=Lesson)
def create_lesson_confirmation_task(sender, instance, created, **kwargs):
    """
    Создаёт задачу менеджеру на подтверждение занятия за 1 день до начала.
    """
    if not created:
        return  # Только при создании нового занятия
    
    if not instance.client:
        return
    
    # Рассчитываем дедлайн — за 1 день до начала занятия (18:00 предыдущего дня)
    deadline = instance.start_time - timedelta(days=1)
    deadline = deadline.replace(hour=18, minute=0, second=0, microsecond=0)
    
    # Если дедлайн уже прошёл — создаём задачу с дедлайном "через 1 час"
    if deadline < timezone.now():
        deadline = timezone.now() + timedelta(hours=1)
    
    # === ИСПРАВЛЕНО: Назначаем задачу создателю занятия (если известен) ===
    # Если создатель не определён — берём первого менеджера
    if instance.created_by:
        assigned_to = instance.created_by.user
    else:
        managers = UserProfile.objects.filter(role__in=['owner', 'admin', 'manager'])
        assigned_to = managers.first().user if managers.exists() else None
    
    # Создаём задачу, привязанную к занятию
    Interaction.objects.create(
        client=instance.client,
        interaction_type='task',
        content=f"📞 Подтвердить занятие {instance.start_time.strftime('%d.%m в %H:%M')} ({instance.room.name})",
        deadline=deadline,
        assigned_to=assigned_to,
        created_by=assigned_to,
        is_reminder=True,
        lesson=instance,
    )