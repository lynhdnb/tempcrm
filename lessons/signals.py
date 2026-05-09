from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import Lesson, LessonType, Attendance


@receiver(post_save, sender=Lesson)
def auto_calculate_end_time(sender, instance, **kwargs):
    """
    Автоматический расчет времени окончания занятия
    Если не указано явно, используем duration_default из LessonType
    """
    if not instance.end_time and instance.start_time and instance.lesson_type:
        end_time = instance.start_time + timedelta(minutes=instance.lesson_type.duration_default)
        Lesson.objects.filter(pk=instance.pk).update(end_time=end_time)


@receiver(post_save, sender=Lesson)
def auto_create_attendance(sender, instance, created, **kwargs):
    """
    Автоматическое создание записи посещаемости при создании занятия
    """
    if created and not hasattr(instance, 'attendance'):
        Attendance.objects.create(
            lesson=instance,
            is_present=False,  # По умолчанию не пришел
            notes=""
        )


@receiver(post_save, sender=Attendance)
def update_lesson_status_on_attendance(sender, instance, **kwargs):
    """
    Обновление статуса занятия при изменении посещаемости
    """
    if instance.lesson and instance.is_present:
        # Если ученик присутствовал, обновляем примечание о проведении
        Lesson.objects.filter(pk=instance.lesson.pk).update(
            updated_at=timezone.now()
        )


@receiver(pre_save, sender=Lesson)
def check_lesson_conflicts(sender, instance, **kwargs):
    """
    Проверка на конфликты расписания (опционально)
    Можно включить для проверки пересечений занятий в одном времени
    """
    if instance.pk:  # Обновление существующего
        return
        
    # Проверка на пересечения с другими занятиями для того же ученика
    conflicting_lessons = Lesson.objects.filter(
        client=instance.client,
        status='planned'
    ).exclude(pk=instance.pk).filter(
        start_time__lt=instance.end_time,
        end_time__gt=instance.start_time
    )
    
    if conflicting_lessons.exists():
        # Можно поднять исключение или просто проигнорировать
        # raise ValidationError("Конфликт расписания для этого ученика")
        pass


@receiver(post_save, sender=Lesson)
def notify_about_upcoming_lesson(sender, instance, created, **kwargs):
    """
    Уведомление о предстоящем занятии
    Запускается за 24 часа до занятия
    """
    if instance.status == 'planned':
        from datetime import timedelta
        hours_until = (instance.start_time - timezone.now()).total_seconds() / 3600
        
        if created and 23 <= hours_until <= 25:
            # TODO: Отправить уведомление учителю и ученику
            # Это должно быть через Celery task
            pass
