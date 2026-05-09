from django.db import models
from django.contrib.auth.models import User
from core.models import Client, Enrollment
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class PaymentMethod(models.Model):
    """Способы оплаты"""
    name = models.CharField("Название", max_length=50, unique=True)
    code = models.SlugField("Код", unique=True, help_text="Для внутренних операций")
    icon = models.CharField("Иконка (emoji/css)", max_length=20, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    requires_contract = models.BooleanField("Требуется договор", default=False)
    
    # Настройки комиссий
    commission_percentage = models.DecimalField(
        "Комиссия (%)", 
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Комиссия платежной системы в процентах"
    )
    
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Способ оплаты"
        verbose_name_plural = "Способы оплаты"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} {self.icon}"


class PaymentPackage(models.Model):
    """Пакеты уроков для продажи"""
    name = models.CharField("Название пакета", max_length=100)
    slug = models.SlugField("Слаг", unique=True)
    
    lesson_type = models.ForeignKey(
        'lessons.LessonType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='packages',
        verbose_name="Тип занятий"
    )
    
    lesson_count = models.PositiveIntegerField("Количество занятий")
    price = models.DecimalField("Цена (руб)", max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(
        "Скидка (%)", 
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Скидка при покупке пакета"
    )
    
    validity_days = models.PositiveIntegerField(
        "Действителен (дней)", 
        default=90,
        help_text="Срок действия пакета с момента покупки"
    )
    
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активен", default=True)
    is_popular = models.BooleanField("Популярный", default=False, help_text="Для выделения в прайсе")
    
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Пакет уроков"
        verbose_name_plural = "Пакеты уроков"
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - {self.lesson_count} занятий"
    
    @property
    def price_per_lesson(self):
        """Цена за одно занятие"""
        return self.price / self.lesson_count
    
    @property
    def discounted_price(self):
        """Цена со скидкой"""
        discount = self.price * self.discount_percentage / 100
        return self.price - discount


class Contract(models.Model):
    """Договор с клиентом"""
    STATUS_CHOICES = [
        ('DRAFT', 'Черновик'),
        ('ACTIVE', 'Активен'),
        ('SUSPENDED', 'Приостановлен'),
        ('COMPLETED', 'Завершен'),
        ('TERMINATED', 'Расторгнут'),
    ]
    
    contract_number = models.CharField(
        "Номер договора", 
        max_length=20, 
        unique=True,
        editable=False
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contracts', verbose_name="Клиент")
    
    start_date = models.DateField("Дата начала")
    end_date = models.DateField("Дата окончания", null=True, blank=True)
    
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Условия
    lesson_package = models.ForeignKey(
        PaymentPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracts',
        verbose_name="Пакет уроков"
    )
    monthly_fee = models.DecimalField(
        "Ежемесячная плата (руб)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Для рассрочки или абонемента"
    )
    
    # Документы
    contract_file = models.FileField(
        "Файл договора",
        upload_to='contracts/%Y/%m/',
        null=True,
        blank=True
    )
    
    notes = models.TextField("Примечания", blank=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_contracts'
    )
    
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Договор"
        verbose_name_plural = "Договоры"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status', 'client']),
        ]

    def save(self, *args, **kwargs):
        # Автоматическая генерация номера договора
        if not self.contract_number:
            from django.utils import timezone
            year = timezone.now().year
            last_contract = Contract.objects.filter(
                contract_number__startswith=f"CTR-{year}-"
            ).order_by('-contract_number').first()
            
            if last_contract:
                last_num = int(last_contract.contract_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.contract_number = f"CTR-{year}-{new_num:04d}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.contract_number} - {self.client}"


class Payment(models.Model):
    """Оплата"""
    STATUS_CHOICES = [
        ('PENDING', 'Ожидает'),
        ('COMPLETED', 'Завершена'),
        ('CANCELLED', 'Отменена'),
        ('REFUNDED', 'Возвращена'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('ONCE', 'Разовый платёж'),
        ('BANK_2', 'Банковская рассрочка 2 платежа'),
        ('BANK_3', 'Банковская рассрочка 3 платежа'),
        ('BANK_6', 'Банковская рассрочка 6 платежей'),
        ('SCHOOL_2', 'Рассрочка школы 2 платежа'),
        ('SCHOOL_3', 'Рассрочка школы 3 платежа'),
        ('SCHOOL_6', 'Рассрочка школы 6 платежей'),
    ]
    
    payment_type = models.CharField(
        "Тип оплаты",
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='ONCE'
    )
    
    installment_number = models.PositiveIntegerField(
        "№ платежа",
        null=True,
        blank=True,
        help_text="Для рассрочки: 1/2, 2/2 и т.д."
    )
    
    total_installments = models.PositiveIntegerField(
        "Всего платежей",
        null=True,
        blank=True,
        help_text="Общее количество платежей в рассрочке"
    )
    
    bank_fee_percent = models.DecimalField(
        "Комиссия банка (%)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Комиссия платежной системы в процентах"
    )
    
    bank_fee_amount = models.DecimalField(
        "Сумма комиссии (руб)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Фактическая сумма комиссии"
    )
    
    amount = models.DecimalField("Сумма (руб)", max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(
        "Уже оплачено (руб)",
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments',
        verbose_name="Способ оплаты"
    )
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='payments', verbose_name="Клиент")
    contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name="Договор"
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name="Запись на курс"
    )
    
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Детали платежа
    description = models.TextField("Описание", blank=True)
    invoice_number = models.CharField("Номер счета", max_length=50, blank=True)
    
    # Даты
    due_date = models.DateField("Срок оплаты", null=True, blank=True)
    paid_at = models.DateTimeField("Время оплаты", null=True, blank=True)
    
    # Для возвратов
    refund_reason = models.TextField("Причина возврата", blank=True)
    refunded_at = models.DateTimeField("Время возврата", null=True, blank=True)
    
    # Комментарии
    notes = models.TextField("Внутренние примечания", blank=True)
    
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_payments',
        verbose_name="Обработал"
    )
    
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплата"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['status', 'due_date']),
        ]

    def __str__(self):
        return f"{self.get_status_display()}: {self.amount} руб. - {self.client}"
    
    @property
    def remaining_amount(self):
        """Оставшаяся сумма к оплате"""
        return self.amount - self.paid_amount
    
    @property
    def is_paid(self):
        """Полностью ли оплачено"""
        return self.paid_amount >= self.amount
    
    @property
    def is_overdue(self):
        """Просрочена ли оплата"""
        from django.utils import timezone
        if self.due_date and self.status == 'PENDING':
            return timezone.now().date() > self.due_date
        return False


class Invoice(models.Model):
    """Счет на оплату"""
    STATUS_CHOICES = [
        ('DRAFT', 'Черновик'),
        ('SENT', 'Отправлен'),
        ('PAID', 'Оплачен'),
        ('CANCELLED', 'Отменен'),
    ]
    
    invoice_number = models.CharField(
        "Номер счета", 
        max_length=50,
        unique=True,
        editable=False
    )
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices', verbose_name="Клиент")
    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice',
        verbose_name="Оплата"
    )
    
    amount = models.DecimalField("Сумма (руб)", max_digits=10, decimal_places=2)
    
    due_date = models.DateField("Срок оплаты")
    issued_date = models.DateField("Дата выставления", auto_now_add=True)
    
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Детали
    description = models.TextField("Описание", blank=True)
    items = models.JSONField("Позиции", blank=True, default=list, help_text="[{\"name\": \"Пакет 8 занятий\", \"quantity\": 1, \"price\": 5000}]")
    
    # Отправка
    sent_at = models.DateTimeField("Отправлен", null=True, blank=True)
    sent_to_email = models.EmailField("Отправлено на email", blank=True)
    
    # Документы
    pdf_file = models.FileField(
        "PDF файл",
        upload_to='invoices/%Y/%m/',
        null=True,
        blank=True
    )
    
    notes = models.TextField("Примечания", blank=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices'
    )
    
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Счет"
        verbose_name_plural = "Счета"
        ordering = ['-issued_date']

    def save(self, *args, **kwargs):
        # Автоматическая генерация номера счета
        if not self.invoice_number:
            from django.utils import timezone
            year = timezone.now().year
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=f"INV-{year}-"
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.invoice_number = f"INV-{year}-{new_num:04d}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.amount} руб. - {self.client}"
    
    @property
    def is_overdue(self):
        """Просрочен ли счет"""
        from django.utils import timezone
        return self.status in ['DRAFT', 'SENT'] and timezone.now().date() > self.due_date
