from django.db import models
from django.contrib.auth.models import User
from core.models import Client

class Task(models.Model):
    """Задачи для сотрудников"""
    PRIORITY_CHOICES = [
        ('LOW', 'Низкий'),
        ('MEDIUM', 'Средний'),
        ('HIGH', 'Высокий'),
        ('URGENT', 'Срочно'),
    ]
    STATUS_CHOICES = [
        ('TODO', 'К выполнению'),
        ('IN_PROGRESS', 'В процессе'),
        ('REVIEW', 'На проверке'),
        ('DONE', 'Выполнено'),
        ('CANCELLED', 'Отменено'),
    ]

    title = models.CharField("Заголовок", max_length=200)
    description = models.TextField("Описание", blank=True)
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks', verbose_name="Клиент (если применимо)")
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_tasks', verbose_name="Исполнитель")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks', editable=False, verbose_name="Постановщик")
    
    priority = models.CharField("Приоритет", max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='TODO')
    
    due_date = models.DateTimeField("Дедлайн", null=True, blank=True)
    completed_at = models.DateTimeField("Выполнено", null=True, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['-priority', 'due_date']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"

    def save(self, *args, **kwargs):
        if self.status == 'DONE' and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        elif self.status != 'DONE':
            self.completed_at = None
        super().save(*args, **kwargs)