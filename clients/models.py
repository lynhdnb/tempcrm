from django.db import models
from django.contrib.auth.models import User

class Client(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('active', 'Активный'),
        ('inactive', 'Неактивный'),
    ]
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    phone = models.CharField('Телефон', max_length=20, db_index=True)
    email = models.EmailField('Email', blank=True, db_index=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new', db_index=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True, db_index=True)
    
# Новое поле:
#    manager = models.ForeignKey(
#        User,
#        on_delete=models.SET_NULL,
##        null=True,
#        blank=True,
#        verbose_name='Менеджер'
#    )

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']

class Interaction(models.Model):
    TYPE_CHOICES = [
        ('note', 'Комментарий'),
        ('task', 'Задача'),
        ('call', 'Звонок'),
        ('enrollment', 'Запись на занятие'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='Клиент', db_index=True)
    interaction_type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES, db_index=True)
    
    # Основное содержание
    content = models.TextField('Содержание', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    created_at = models.DateTimeField('Дата', auto_now_add=True)

    # --- Для комментариев ---
    original_content = models.TextField('Исходный текст', blank=True)
    is_edited = models.BooleanField('Отредактирован', default=False)
    can_edit = models.BooleanField('Можно редактировать', default=True)

    # --- Для задач ---
    deadline = models.DateTimeField('Дедлайн', null=True, blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_interactions',
        verbose_name='Назначена'
    )
    is_reminder = models.BooleanField('Напоминание', default=False)
    is_completed = models.BooleanField('Выполнено', default=False)  # <-- новое поле

    # --- Для звонков ---
    call_initiated_at = models.DateTimeField('Время начала звонка', null=True, blank=True)
    call_logged_at = models.DateTimeField('Время фиксации результата', null=True, blank=True)

    # --- Для записей ---
    enrollment = models.ForeignKey(
        'products.Enrollment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Запись на продукт'
    )
    
    lesson = models.ForeignKey(
        'lessons.Lesson',           
        on_delete=models.CASCADE,   # Если занятие удалят → задача тоже удалится
        null=True,
        blank=True,
        verbose_name='Занятие'      # Название для админки
    )
    
    def __str__(self):
        return f"{self.get_interaction_type_display()} — {self.created_at.strftime('%d.%m %Y %H:%M')}"

    class Meta:
        verbose_name = 'Взаимодействие'
        verbose_name_plural = 'Взаимодействия'
        ordering = ['-created_at']
        
class InteractionEdit(models.Model):
    interaction = models.ForeignKey(
        Interaction,
        on_delete=models.CASCADE,
        related_name='edits',
        verbose_name='Взаимодействие'
    )
    edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Изменил'
    )
    old_content = models.TextField('Старый текст')
    new_content = models.TextField('Новый текст')
    edited_at = models.DateTimeField('Дата изменения', auto_now_add=True)

    class Meta:
        verbose_name = 'Правка взаимодействия'
        verbose_name_plural = 'Правки взаимодействий'
        ordering = ['-edited_at']
