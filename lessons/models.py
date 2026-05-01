from django.db import models
from django.utils import timezone
from clients.models import Client
from core.models import UserProfile
from products.models import Enrollment


class Room(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Кабинет'
        verbose_name_plural = 'Кабинеты'


class Lesson(models.Model):
    STATUS_CHOICES = [
        ('scheduled', '📅 Запланировано'),
        ('confirmed', '✅ Подтверждено'),
        ('in_progress', '🔄 В процессе'),
        ('completed', '✔️ Проведено'),
        ('no_show', '❌ Не явился'),
        ('cancelled_early', '⚠️ Отменено заранее'),
    ]
    
    TYPE_CHOICES = [
        ('lesson', 'Занятие с преподавателем'),
        ('practice', 'Самостоятельная практика'),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name='Клиент',
        db_index=True
    )
    teacher = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={'role': 'teacher'},
        verbose_name='Преподаватель',
        db_index=True
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        verbose_name='Кабинет',
        db_index=True
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='Абонемент',
        db_index=True
    )
    lesson_type = models.CharField(
        'Тип',
        max_length=20,
        choices=TYPE_CHOICES,
        default='lesson',
        db_index=True
    )
    status = models.CharField(
        'Статус',
        max_length=30,
        choices=STATUS_CHOICES,
        default='scheduled',
        db_index=True
    )
    start_time = models.DateTimeField('Начало', db_index=True)
    end_time = models.DateTimeField('Окончание')
    notes = models.TextField('Заметки', blank=True)
    
    # Отслеживание списания баланса
    balance_charged = models.BooleanField(
        'Баланс списан',
        default=False,
        help_text='True если занятие уже списало баланс клиента'
    )
    
    # Для аудита изменений статуса
    status_changed_at = models.DateTimeField('Дата изменения статуса', null=True, blank=True)
    status_changed_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons_status_changed',
        verbose_name='Изменил статус'
    )
    
        # Нужно чтобы назначать задачу на подтверждение создателю занятия
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons_created',
        verbose_name='Создал'
    )

    def __str__(self):
        return f"{self.client} — {self.start_time.strftime('%d.%m %H:%M')}"

    def save(self, *args, **kwargs):
        """Переопределяем save для авто-обновления статуса и списания баланса"""
        from django.db import transaction
        
        # Сохраняем старый статус если объект существует
        old_status = None
        if self.pk:
            try:
                old_lesson = Lesson.objects.get(pk=self.pk)
                old_status = old_lesson.status
            except Lesson.DoesNotExist:
                pass
        
        # Авто-обновление статуса по времени (если не установлен вручную)
        now = timezone.now()
        if self.status in ['scheduled', 'confirmed']:
            if now >= self.start_time and now < self.end_time:
                self.status = 'in_progress'
            elif now >= self.end_time and self.status != 'completed':
                # Не авто-завершаем, оставляем scheduled для ручного подтверждения
                pass
        
        # Сохраняем объект
        super().save(*args, **kwargs)
        
        # Обновляем баланс при смене статуса
        if old_status != self.status:
            self._update_balance(old_status)

    def _update_balance(self, old_status):
        """Обновляет баланс клиента при изменении статуса занятия"""
        if not self.enrollment:
            return
        
        # Статусы которые требуют списания
        charge_statuses = ['completed', 'no_show']
        # Статусы которые требуют возврата
        refund_statuses = ['scheduled', 'confirmed', 'in_progress', 'cancelled_early']
        
        # Определяем нужно ли списывать или возвращать
        should_charge = self.status in charge_statuses and not self.balance_charged
        should_refund = self.status in refund_statuses and self.balance_charged
        
        if should_charge:
            self._charge_balance()
            self.balance_charged = True
            Lesson.objects.filter(pk=self.pk).update(balance_charged=True)
        elif should_refund:
            self._refund_balance()
            self.balance_charged = False
            Lesson.objects.filter(pk=self.pk).update(balance_charged=False)

    def _charge_balance(self):
        """Списывает 1 урок или практику с абонемента"""
        if not self.enrollment:
            return
        
        if self.lesson_type == 'lesson':
            Enrollment.objects.filter(pk=self.enrollment.pk).update(
                lessons_used=models.F('lessons_used') + 1
            )
        elif self.lesson_type == 'practice':
            Enrollment.objects.filter(pk=self.enrollment.pk).update(
                practices_used=models.F('practices_used') + 1
            )

    def _refund_balance(self):
        """Возвращает 1 урок или практику на абонемент"""
        if not self.enrollment:
            return
        
        if self.lesson_type == 'lesson':
            Enrollment.objects.filter(pk=self.enrollment.pk).update(
                lessons_used=models.F('lessons_used') - 1
            )
        elif self.lesson_type == 'practice':
            Enrollment.objects.filter(pk=self.enrollment.pk).update(
                practices_used=models.F('practices_used') - 1
            )

    def get_lesson_number(self):
        """Расчёт номера занятия для отображения"""
        if not self.enrollment:
            return None
        
        from django.db.models import Count, Q
        
        if self.status in ['completed', 'no_show']:
            # Для завершённых или неявок — считаем по факту
            completed_count = Lesson.objects.filter(
                client=self.client,
                enrollment=self.enrollment,
                status__in=['completed', 'no_show'],
                lesson_type=self.lesson_type,
                start_time__lt=self.start_time
            ).count()
            return completed_count + 1
        
        elif self.status in ['scheduled', 'confirmed', 'in_progress']:
            # Для запланированных — completed + порядковый среди scheduled
            completed_count = Lesson.objects.filter(
                client=self.client,
                enrollment=self.enrollment,
                status__in=['completed', 'no_show'],
                lesson_type=self.lesson_type
            ).count()
            
            # Порядковый номер среди будущих занятий (по дате)
            scheduled_before = Lesson.objects.filter(
                client=self.client,
                enrollment=self.enrollment,
                status__in=['scheduled', 'confirmed', 'in_progress'],
                lesson_type=self.lesson_type,
                start_time__lt=self.start_time
            ).count()
            
            return completed_count + scheduled_before + 1
        
        return None
    
    def get_display_number(self):
        """Красивое отображение номера"""
        num = self.get_lesson_number()
        if num:
            if self.status in ['completed', 'no_show']:
                return f"№{num}"
            else:
                return f"№{num} (ожидается)"
        return "—"

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['-start_time']