from django.db import models
from django.contrib.auth.models import User
from core.models import Client, EmployeeProfile, Enrollment
from django.utils.translation import gettext_lazy as _
from datetime import timedelta

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
    LESSON_TYPE_CHOICES = [
        ('STANDARD', 'Занятие с преподавателем'),
        ('PRACTICE', 'Самостоятельная практика'),
    ]

    STATUS_CHOICES = [
        ('planned', 'Запланировано'),
        ('completed', 'Проведено'),
        ('cancelled', 'Отменено'),
        ('no_show', 'Студент не пришёл'),
    ]

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name="Запись на курс",
        null=True,
        blank=True
    )
    
    start_time = models.DateTimeField("Дата и время начала")
    end_time = models.DateTimeField("Дата и время окончания", null=True, blank=True)
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='lessons', verbose_name="Клиент")
    teacher = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons', verbose_name="Преподаватель", help_text="Опционально: не заполняется для самостоятельной практики")
    lesson_type = models.ForeignKey(LessonType, on_delete=models.SET_NULL, null=True, related_name='lessons', verbose_name="Тип занятия")
    
    lesson_type_detail = models.CharField(
        "Тип занятия",
        max_length=20,
        choices=LESSON_TYPE_CHOICES,
        default='STANDARD',
        help_text="Занятие с преподавателем или самостоятельная практика"
    )
    
    duration_minutes = models.PositiveIntegerField("Длительность (минут)", default=60)
    
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='planned')
    comment = models.TextField("Комментарий", blank=True)
    
    # Кто отметил проведение
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_lessons')
    marked_at = models.DateTimeField(null=True, blank=True)
    
    # Отмена
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_lessons')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=100, blank=True)
    
    # Для переноса занятий
    parent_lesson = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='rescheduled_from', verbose_name="Исходное занятие")
    
    # Аудитория и ресурсы
    room = models.ForeignKey(
        'core.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        verbose_name="Аудитория"
    )
    
    # Ресурсы (многие ко многим)
    resources = models.ManyToManyField(
        'core.Resource',
        related_name='lessons',
        blank=True,
        verbose_name="Оборудование"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['start_time']),
            models.Index(fields=['teacher', 'start_time']),
            models.Index(fields=['client', 'start_time']),
        ]

    def __str__(self):
        type_text = "Самост." if self.lesson_type_detail == 'PRACTICE' else "Урок"
        return f"{self.client} - {type_text} ({self.start_time})"

    def save(self, *args, **kwargs):
        # Автоматическая установка teacher для самостоятельной практики
        if self.lesson_type_detail == 'PRACTICE':
            self.teacher = None
        
        # Автоматический расчет времени окончания, если не указано
        if not self.end_time and self.start_time:
            self.end_time = self.start_time + timedelta(minutes=self.duration_minutes)
        
        super().save(*args, **kwargs)

        # Обновить прогресс при изменении статуса на completed
        if self.enrollment and self.status == 'completed' and self.lesson_type_detail == 'STANDARD':
            self.enrollment.update_progress()

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