from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class Product(models.Model):
    TYPE_CHOICES = [
        ('lesson', 'Индивидуальное занятие'),
        ('course', 'Курс'),
        ('certificate', 'Подарочный сертификат'),
        ('studio_rental', 'Аренда студии'),
        ('trial', 'Пробное занятие'),
    ]

    name = models.CharField('Название', max_length=200)
    product_type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES)
    
    # Базовые лимиты
    base_lessons = models.PositiveIntegerField('Базовое количество занятий', default=0)
    base_practices = models.PositiveIntegerField('Базовое количество практик', default=0)
    
    # Безлимитная практика
    unlimited_practice = models.BooleanField('Безлимитная практика', default=False)
    unlimited_duration_months = models.PositiveIntegerField(
        'Срок безлимита (мес)', 
        default=0,
        help_text='Если безлимит включён, указывается срок в месяцах'
    )
    
    # Цена
    default_price = models.DecimalField(
        'Цена по умолчанию',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Архив
    is_archived = models.BooleanField('Архивный', default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['name']

from clients.models import Client

class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('completed', 'Завершён'),
        ('archived', 'Архив'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='Клиент', db_index=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Продукт (шаблон)', db_index=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    # Фактические лимиты (могут отличаться от шаблона)
    lessons_total = models.PositiveIntegerField('Всего занятий', default=0)
    lessons_used = models.PositiveIntegerField('Использовано занятий', default=0)
    
    practices_total = models.PositiveIntegerField('Всего практик', default=0)
    practices_used = models.PositiveIntegerField('Использовано практик', default=0)
    
    # Безлимитная практика
    unlimited_practice = models.BooleanField('Безлимитная практика', default=False)
    unlimited_end_date = models.DateField(
        'Окончание безлимита',
        null=True,
        blank=True,
        help_text='Если безлимит включён, указывается дата окончания'
    )
    
    # Цена и оплата
    price = models.DecimalField(
        'Фактическая цена',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Рассрочка
    installment_parts = models.PositiveSmallIntegerField(
        'Количество платежей при рассрочке',
        null=True,
        blank=True,
        help_text='Оставьте пустым для единовременной оплаты. Максимум — 12.'
    )

    is_paid = models.BooleanField('Оплачен полностью', default=False)
    
    # Статус и сроки
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField('Дата начала', auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client} — {self.product.name}"

    def create_installment_payments_and_tasks(self, payment_method_id=None, created_by_user=None):
        """
        Создаёт платежи и задачи для внутренней рассрочки.
        Вызывается после сохранения Enrollment, если указано количество платежей.
        """
        from .models import Payment, PaymentMethod
        from datetime import date, timedelta

        if not self.installment_parts or self.installment_parts < 2:
            return  # Нет рассрочки или всего 1 платёж — ничего не создаём

        parts = min(self.installment_parts, 12)  # Ограничение сверху
        total_amount = self.price

        payment_method = None
        if payment_method_id:
            try:
                payment_method = PaymentMethod.objects.get(id=payment_method_id)
            except PaymentMethod.DoesNotExist:
                pass

        start_date = date.today()
        interval = 30  # ~30 дней между платежами

        for i in range(1, parts + 1):
            due_date = start_date + timedelta(days=interval * (i - 1))
            amount_per_part = total_amount / parts

            method_name = payment_method.name if payment_method else "Рассрочка (школа)"
            p_type = payment_method.payment_type if payment_method else "cash"
            comm_pct = payment_method.commission_percent if payment_method else 0
            comm_fix = payment_method.commission_fixed if payment_method else 0

            amount_received = amount_per_part  # Внутренняя рассрочка — без комиссии

            # Определяем, оплачен ли платёж
            if i == 1:
                # Первый платёж — сразу оплачивается
                payment_is_paid = True
                payment_paid_at = timezone.now()
            else:
                payment_is_paid = False
                payment_paid_at = None

            payment = Payment.objects.create(
                enrollment=self,
                amount_paid_by_client=amount_per_part,
                amount_received=amount_received,
                payment_method_name=method_name,
                payment_type=p_type,
                commission_percent_used=comm_pct,
                commission_fixed_used=comm_fix,
                is_installment=True,
                installment_number=i,
                due_date=due_date,
                is_paid=payment_is_paid,
                paid_at=payment_paid_at
            )

            if created_by_user:
                from clients.models import Interaction
                Interaction.objects.create(
                    client=self.client,
                    interaction_type='task',
                    content=f"Забрать платёж №{i} от {self.client}",
                    deadline=due_date,
                    assigned_to=created_by_user,
                    created_by=created_by_user,
                    is_reminder=True
                )

    class Meta:
        verbose_name = 'Запись на продукт'
        verbose_name_plural = 'Записи на продукты'
        ordering = ['-created_at']

class PaymentMethod(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('cash', 'Наличные'),
        ('card_transfer', 'Перевод на карту'),
        ('bank_account', 'Расчётный счёт'),
    ]

    name = models.CharField('Название способа оплаты', max_length=100)
    payment_type = models.CharField('Тип оплаты', max_length=20, choices=PAYMENT_TYPE_CHOICES)
    commission_percent = models.DecimalField(
        'Комиссия (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Например: 1.5 для 1.5%'
    )
    commission_fixed = models.DecimalField(
        'Фиксированная комиссия (₽)',
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Например: 30 для 30 ₽'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Способ оплаты'
        verbose_name_plural = 'Способы оплаты'
        ordering = ['name']

class Payment(models.Model):
    enrollment = models.ForeignKey('Enrollment', on_delete=models.CASCADE, verbose_name='Запись на продукт', db_index=True)
    is_paid = models.BooleanField('Оплачен', default=False, db_index=True)
    
    # Суммы
    amount_paid_by_client = models.DecimalField(
        'Сумма от клиента',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    amount_received = models.DecimalField(
        'Сумма получена школой',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Скопированные данные из PaymentMethod на момент создания
    payment_method_name = models.CharField('Способ оплаты (на момент оплаты)', max_length=100)
    payment_type = models.CharField('Тип оплаты (на момент оплаты)', max_length=20)
    commission_percent_used = models.DecimalField(
        'Использованная комиссия (%)',
        max_digits=5,
        decimal_places=2,
        default=0
    )
    commission_fixed_used = models.DecimalField(
        'Использованная фикс. комиссия (₽)',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Для рассрочки
    is_installment = models.BooleanField('Рассрочка', default=False)
    installment_number = models.PositiveIntegerField('Номер платежа', null=True, blank=True)
    due_date = models.DateField('Дата платежа, план', null=True, blank=True)
    
    # Статус
    is_paid = models.BooleanField('Оплачен', default=False)
    paid_at = models.DateTimeField('Дата оплаты, факт', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Оплачен" if self.is_paid else "Не оплачен"
        return f"{self.amount_paid_by_client} ₽ → {self.amount_received} ₽ — {status}"

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'
        ordering = ['-due_date', '-created_at']
