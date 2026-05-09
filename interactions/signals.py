from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Interaction, InteractionType, Comment
from core.models import Client


@receiver(post_save, sender=Interaction)
def update_client_interaction_date(sender, instance, created, **kwargs):
    """
    Обновление даты последнего взаимодействия у клиента
    Когда создается новое взаимодействие
    """
    if created and instance.client and instance.date_time:
        client = instance.client
        interaction_date = instance.date_time.date()
        
        # Проверяем текущую дату последнего взаимодействия
        current_last = Client.objects.values_list('last_interaction_date', 'status').filter(pk=client.pk).first()
        
        if current_last:
            current_date, current_status = current_last
            
            # Обновляем только если новая дата больше или если нет даты
            if not current_date or interaction_date > current_date:
                # Обновляем дату и автоматически обновляем статус
                Client.objects.filter(pk=client.pk).update(
                    last_interaction_date=interaction_date
                )
                
                # Пересчитываем silent_days и статус
                silent_days = (timezone.now().date() - interaction_date).days
                new_status = current_status
                
                if silent_days > 30:
                    new_status = 'LOST'
                elif silent_days > 14:
                    new_status = 'SILENT'
                elif silent_days <= 14 and current_status in ['SILENT', 'LOST']:
                    new_status = 'ACTIVE'
                
                Client.objects.filter(pk=client.pk).update(
                    silent_days=silent_days,
                    status=new_status
                )


@receiver(pre_save, sender=Interaction)
def set_default_interaction_date(sender, instance, **kwargs):
    """
    Устанавливает текущую дату и время, если не указано
    """
    if not instance.date_time:
        instance.date_time = timezone.now()


@receiver(post_save, sender=Interaction)
def notify_about_reminder(sender, instance, created, **kwargs):
    """
    Можно добавить отправку уведомлений для напоминаний
    Здесь будет интеграция с email/SMS
    """
    if created and instance.is_reminder and instance.reminder_date:
        # TODO: Добавить отправку уведомления
        # from django.core.mail import send_mail
        # send_mail(...)
        pass


@receiver(post_save, sender=Comment)
def update_interaction_updated_at(sender, instance, **kwargs):
    """
    Обновляет updated_at у Interaction когда добавляется комментарий
    """
    if instance.interaction:
        from django.utils import timezone
        Interaction.objects.filter(pk=instance.interaction.pk).update(
            updated_at=timezone.now()
        )
