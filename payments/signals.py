from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal

from .models import Payment, Invoice, PaymentPackage, Contract
from core.models import Client


@receiver(post_save, sender=Payment)
def update_payment_status_on_full_payment(sender, instance, **kwargs):
    """
    Автоматическое обновление статуса оплаты при полной оплате
    """
    if instance.paid_amount >= instance.amount and instance.status != 'COMPLETED':
        Payment.objects.filter(pk=instance.pk).update(
            status='COMPLETED',
            paid_at=timezone.now()
        )


@receiver(pre_save, sender=Payment)
def validate_payment_amount(sender, instance, **kwargs):
    """
    Валидация суммы оплаты
    """
    if instance.amount <= 0:
        raise ValueError("Сумма оплаты должна быть больше нуля")
    
    if instance.paid_amount < 0:
        raise ValueError("Уже оплаченная сумма не может быть отрицательной")
    
    if instance.paid_amount > instance.amount:
        raise ValueError("Уже оплаченная сумма не может превышать общую сумму")


@receiver(post_save, sender=Payment)
def update_client_payment_history(sender, instance, created, **kwargs):
    """
    Обновление истории платежей клиента (можно добавить для аналитики)
    """
    if created and instance.client and instance.status == 'COMPLETED':
        # TODO: Можно добавить логику для обновления статистики клиента
        # Например: last_payment_date, total_paid, etc.
        pass


@receiver(post_save, sender=Invoice)
def auto_update_payment_status_on_invoice_payment(sender, instance, **kwargs):
    """
    Автоматическое обновление статуса связанного платежа при оплате счета
    """
    if instance.payment and instance.status == 'PAID':
        Payment.objects.filter(pk=instance.payment.pk).update(
            status='COMPLETED',
            paid_at=timezone.now()
        )


@receiver(pre_save, sender=Invoice)
def auto_set_payment_status_on_invoice_creation(sender, instance, **kwargs):
    """
    Автоматическое создание платежа при создании счета
    """
    if not instance.payment and instance.status == 'SENT':
        payment = Payment.objects.create(
            client=instance.client,
            amount=instance.amount,
            description=instance.description,
            invoice_number=instance.invoice_number,
            status='PENDING',
            due_date=instance.due_date
        )
        # Обновляем ссылку (но это вызовет рекурсию, поэтому лучше сделать через ID)
        # Invoice.objects.filter(pk=instance.pk).update(payment=payment)


@receiver(post_save, sender=Contract)
def auto_create_initial_payment(sender, instance, created, **kwargs):
    """
    Автоматическое создание начального платежа при создании договора с пакетом
    """
    if created and instance.lesson_package and not instance.payments.exists():
        Payment.objects.create(
            client=instance.client,
            contract=instance,
            amount=instance.lesson_package.price,
            payment_type='PACKAGE',
            description=f"Оплата пакета: {instance.lesson_package.name}",
            status='PENDING',
            due_date=instance.start_date
        )


@receiver(post_save, sender=PaymentPackage)
def update_related_packages(sender, instance, **kwargs):
    """
    При обновлении пакета можно уведомить о изменении цены
    """
    if instance.is_active and instance._state.adding is False:
        # TODO: Логика обновления цен для активных договоров
        pass


# Автоматическая проверка просроченных платежей
def check_overdue_payments():
    """
    Функция для проверки просроченных платежей
    Должна вызываться через Celery beat ежедневно
    """
    from django.utils import timezone
    
    today = timezone.now().date()
    overdue_payments = Payment.objects.filter(
        status='PENDING',
        due_date__lt=today
    )
    
    updated_count = 0
    for payment in overdue_payments:
        # Можно отправить напоминание клиенту
        # Можно обновить статус на CANCELLED если просрочено слишком долго
        updated_count += 1
    
    return updated_count


def check_overdue_invoices():
    """
    Функция для проверки просроченных счетов
    Должна вызываться через Celery beat ежедневно
    """
    from django.utils import timezone
    
    today = timezone.now().date()
    overdue_invoices = Invoice.objects.filter(
        status__in=['DRAFT', 'SENT'],
        due_date__lt=today
    )
    
    updated_count = 0
    for invoice in overdue_invoices:
        # Можно автоматически перевести в CANCELLED
        # или отправить напоминание
        updated_count += 1
    
    return updated_count
