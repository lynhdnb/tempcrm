from django.db import models
from django.contrib.auth.models import User
from core.models import Client, EmployeeProfile
from django.utils.translation import gettext_lazy as _

class LessonType(models.Model):
    """Тип занятия (например, Фортепиано, Вокал, Гитара)"""
    name = models.CharField("Название", max_length=50, unique=True)
    slug = models.SlugField("Слаг", unique=True)
    color = models.CharField("Цвет в календаре", max_length=7, default="#3788d8", help_text="HEX код цвета")
    duration_default = models.PositiveIntegerField("Длительность по умолчанию (мин)", default=60)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Тип занятия"
        verbose_name_plural = "Типы занятий"
        ordering = ['name']

    def __str__(self):
        return self.name

class Lesson(models.Model):
    """Модель занятия"""
    STATUS_CHOICES = [
        ('planned', 'Запланировано'),
        ('completed', 'Проведено'),
        ('cancelled', 'Отменено'),
        ('rescheduled', 'Перенесено'),
    ]

    start_time = models.DateTimeField("Дата и время начала")
    end_time = models.DateTimeField("Дата и время окончания", null=True, blank=True)
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='lessons', verbose_name="Клиент")
    teacher = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='lessons', verbose_name="Преподаватель")
    lesson_type = models.ForeignKey(LessonType, on_delete=models.SET_NULL, null=True, related_name='lessons', verbose_name="Тип занятия")
    
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='planned')
    comment = models.TextField("Комментарий", blank=True)
    
    # Для переноса занятий
    parent_lesson = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='rescheduled_from', verbose_name="Исходное занятие")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"
        ordering = ['-start_time']
        indexes = [models.Index(fields=['start_time'])]

    def __str__(self):
        return f"{self.client} - {self.lesson_type} ({self.start_time})"

    def save(self, *args, **kwargs):
        # Автоматический расчет времени окончания, если не указано
        if not self.end_time and self.start_time and self.lesson_type:
            from datetime import timedelta
            self.end_time = self.start_time + timedelta(minutes=self.lesson_type.duration_default)
        elif not self.end_time and self.start_time:
            from datetime import timedelta
            self.end_time = self.start_time + timedelta(minutes=60)
        super().save(*args, **kwargs)

class Attendance(models.Model):
    """Посещаемость занятия"""
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='attendance', verbose_name="Занятие")
    is_present = models.BooleanField("Присутствовал", default=False)
    notes = models.TextField("Заметки о занятии", blank=True)
    homework = models.TextField("Домашнее задание", blank=True)
    recorded_at = models.DateTimeField("Время записи", auto_now_add=True)

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"

    def __str__(self):
        status = "Присутствовал" if self.is_present else "Отсутствовал"
        return f"{self.lesson.client} - {status}"