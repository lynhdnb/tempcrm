from django.db import models
from django.contrib.auth.models import User
from core.models import Client

class InteractionType(models.Model):
    """Типы взаимодействий (Звонок, Встреча, Сообщение и т.д.)"""
    name = models.CharField("Название", max_length=50, unique=True)
    icon = models.CharField("Иконка (emoji/css)", max_length=20, blank=True, help_text="Например: 📞, ✉️")
    color = models.CharField("Цвет", max_length=7, default="#6c757d", help_text="Hex цвет для визуализации")

    class Meta:
        verbose_name = "Тип взаимодействия"
        verbose_name_plural = "Типы взаимодействий"
        ordering = ['name']

    def __str__(self):
        return self.name

class Interaction(models.Model):
    """История взаимодействий с клиентом"""
    STATUS_CHOICES = [
        ('PLANNED', 'Запланировано'),
        ('COMPLETED', 'Выполнено'),
        ('CANCELLED', 'Отменено'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='interactions', verbose_name="Клиент")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_interactions', verbose_name="Создал")
    interaction_type = models.ForeignKey(InteractionType, on_delete=models.SET_NULL, null=True, related_name='interactions', verbose_name="Тип")
    
    subject = models.CharField("Тема", max_length=200, blank=True)
    note = models.TextField("Заметки", blank=True)
    
    date_time = models.DateTimeField("Дата и время", null=True, blank=True, help_text="Если не указано, считается событием без точного времени")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    
    is_reminder = models.BooleanField("Напоминание", default=False)
    reminder_date = models.DateTimeField("Дата напоминания", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Взаимодействие"
        verbose_name_plural = "Взаимодействия"
        ordering = ['-date_time', '-created_at']
        indexes = [
            models.Index(fields=['client', '-date_time']),
            models.Index(fields=['status', 'is_reminder']),
        ]

    def __str__(self):
        return f"{self.get_status_display()}: {self.subject or self.interaction_type} ({self.client})"

class Comment(models.Model):
    """Комментарии к взаимодействиям (для обсуждений внутри команды)"""
    interaction = models.ForeignKey(Interaction, on_delete=models.CASCADE, related_name='comments', verbose_name="Взаимодействие")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    text = models.TextField("Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.interaction}"


class Notification(models.Model):
    """Уведомления для клиентов и сотрудников"""
    TYPE_CHOICES = [
        ('LESSON_REMINDER_24H', 'Напоминание о занятии за 24 часа'),
        ('LESSON_REMINDER_3H', 'Напоминание о занятии за 3 часа'),
        ('PAYMENT_REMINDER', 'Напоминание об оплате'),
        ('COURSE_COMPLETED', 'Курс завершён'),
        ('CUSTOM', 'Произвольное уведомление'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Ожидает отправки'),
        ('SENT', 'Отправлено'),
        ('FAILED', 'Ошибка отправки'),
    ]
    
    SEND_METHOD_CHOICES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push-уведомление'),
        ('WHATSAPP', 'WhatsApp'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='notifications', verbose_name="Клиент")
    lesson = models.ForeignKey('lessons.Lesson', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications', verbose_name="Занятие")
    enrollment = models.ForeignKey('core.Enrollment', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications', verbose_name="Запись на курс")
    
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField("Заголовок", max_length=200)
    message = models.TextField("Текст")
    
    send_method = models.CharField("Способ", max_length=20, choices=SEND_METHOD_CHOICES, default='EMAIL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    
    scheduled_for = models.DateTimeField("Планируемая отправка", null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.client}"