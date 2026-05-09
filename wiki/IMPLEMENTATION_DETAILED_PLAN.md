# 📋 Детальный план реализации улучшений DJ CRM v2

## 📌 Обзор

Этот документ содержит пошаговый план интеграции лучших практик из AlfaCRM в DJ CRM v2. Каждый шаг подробно описан с примерами кода, миграциями, шаблонами и тестами.

---

# 🎯 ЭТАП 1: Абонементы и финансовая аналитика

## Шаг 1.1: Создание модели Абонементов

### 1.1.1 Описание
Абонементы позволяют клиентам покупать пакеты занятий или месячные подписки с автоматическим списанием.

### 1.1.2 Модель данных

```python
# core/models.py

class Subscription(models.Model):
    """Абонементы — помесечные и поурочные"""
    
    SUBSCRIPTION_TYPE_CHOICES = [
        ('MONTHLY', 'Помесячный'),
        ('LESSON_PACK', 'Пакет уроков'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Активен'),
        ('PAUSED', 'На паузе'),
        ('COMPLETED', 'Завершён'),
        ('EXPIRED', 'Истёк'),
        ('CANCELLED', 'Отменён'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('NOT_PAID', 'Не оплачен'),
        ('PARTIAL', 'Частично оплачен'),
        ('PAID', 'Оплачен'),
    ]
    
    # Основные поля
    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Клиент'
    )
    course = models.ForeignKey(
        'Course',
        on_delete=models.SET_NULL,
        null=True,
        related_name='subscriptions',
        verbose_name='Курс'
    )
    
    # Тип и условия
    subscription_type = models.CharField(
        'Тип абонемента',
        max_length=20,
        choices=SUBSCRIPTION_TYPE_CHOICES,
        default='MONTHLY'
    )
    
    # Для пакетов уроков
    total_lessons = models.PositiveIntegerField(
        'Всего уроков в пакете',
        default=10,
        help_text='Количество уроков для пакетов'
    )
    
    # Даты действия
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания', null=True, blank=True)
    
    # Стоимость и оплата
    price = models.DecimalField(
        'Стоимость (руб)',
        max_digits=10,
        decimal_places=2
    )
    discount_percent = models.DecimalField(
        'Скидка (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        blank=True
    )
    
    payment_status = models.CharField(
        'Статус оплаты',
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='NOT_PAID'
    )
    
    # Прогресс
    lessons_consumed = models.PositiveIntegerField(
        'Проведённых уроков',
        default=0
    )
    
    # Статус
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    
    # Дополнительные поля
    notes = models.TextField('Заметки', blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_subscriptions'
    )
    
    # Служебные поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Абонемент'
        verbose_name_plural = 'Абонементы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['subscription_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.client} — {self.get_subscription_type_display()}"
    
    @property
    def final_price(self):
        """Итоговая цена со скидкой"""
        if self.discount_percent:
            return self.price * (1 - self.discount_percent / 100)
        return self.price
    
    @property
    def remaining_lessons(self):
        """Оставшиеся уроки"""
        if self.subscription_type == 'MONTHLY':
            return float('inf')  # Безлимит
        return max(0, self.total_lessons - self.lessons_consumed)
    
    @property
    def progress_percent(self):
        """Процент использования"""
        if self.subscription_type == 'MONTHLY':
            # По дням
            if not self.start_date or not self.end_date:
                return 0
            total_days = (self.end_date - self.start_date).days
            if total_days == 0:
                return 100
            elapsed = (timezone.now().date() - self.start_date).days
            return min(100, max(0, elapsed / total_days * 100))
        else:
            if self.total_lessons == 0:
                return 0
            return (self.lessons_consumed / self.total_lessons) * 100
    
    def consume_lesson(self):
        """Пометить урок как проведённый"""
        if self.remaining_lessons == float('inf'):
            return  # Безлимит, ничего не считаем
        
        self.lessons_consumed += 1
        if self.lessons_consumed >= self.total_lessons:
            self.status = 'COMPLETED'
        self.save()
    
    def pause(self):
        """Поставить абонемент на паузу"""
        self.status = 'PAUSED'
        self.save()
    
    def resume(self):
        """Продлить абонемент после паузы"""
        self.status = 'ACTIVE'
        self.save()


class SubscriptionLog(models.Model):
    """История изменений абонемента"""
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    ACTION_CHOICES = [
        ('CREATED', 'Создан'),
        ('PAUSED', 'Поставлен на паузу'),
        ('RESUMED', 'Продлён'),
        ('COMPLETED', 'Завершён'),
        ('CANCELLED', 'Отменён'),
        ('LESSON_CONSUMED', 'Списан урок'),
        ('PAYMENT_RECEIVED', 'Поступил платёж'),
        ('MODIFIED', 'Изменён'),
    ]
    
    action = models.CharField('Действие', max_length=20, choices=ACTION_CHOICES)
    description = models.TextField('Описание', blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Лог абонемента'
        verbose_name_plural = 'Логи абонемента'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subscription} — {self.get_action_display()}"
```

### 1.1.3 Создание миграции

```bash
python manage.py makemigrations core --name add_subscription_model
```

**Файл миграции:** `core/migrations/0011_subscription_subscriptionlog.py`

```python
# Generated migration
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0010_tariff_alter_clientcomment_options_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_type', models.CharField(choices=[('MONTHLY', 'Помесячный'), ('LESSON_PACK', 'Пакет уроков')], default='MONTHLY', max_length=20, verbose_name='Тип абонемента')),
                ('total_lessons', models.PositiveIntegerField(default=10, verbose_name='Всего уроков в пакете')),
                ('start_date', models.DateField(verbose_name='Дата начала')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='Дата окончания')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Стоимость (руб)')),
                ('discount_percent', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=5, verbose_name='Скидка (%)')),
                ('payment_status', models.CharField(choices=[('NOT_PAID', 'Не оплачен'), ('PARTIAL', 'Частично оплачен'), ('PAID', 'Оплачен')], default='NOT_PAID', max_length=20, verbose_name='Статус оплаты')),
                ('lessons_consumed', models.PositiveIntegerField(default=0, verbose_name='Проведённых уроков')),
                ('status', models.CharField(choices=[('ACTIVE', 'Активен'), ('PAUSED', 'На паузе'), ('COMPLETED', 'Завершён'), ('EXPIRED', 'Истёк'), ('CANCELLED', 'Отменён')], default='ACTIVE', max_length=20, verbose_name='Статус')),
                ('notes', models.TextField(blank=True, verbose_name='Заметки')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='core.client', verbose_name='Клиент')),
                ('course', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subscriptions', to='core.course', verbose_name='Курс')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_subscriptions', to='auth.user')),
            ],
            options={
                'verbose_name': 'Абонемент',
                'verbose_name_plural': 'Абонементы',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SubscriptionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('CREATED', 'Создан'), ('PAUSED', 'Поставлен на паузу'), ('RESUMED', 'Продлён'), ('COMPLETED', 'Завершён'), ('CANCELLED', 'Отменён'), ('LESSON_CONSUMED', 'Списан урок'), ('PAYMENT_RECEIVED', 'Поступил платёж'), ('MODIFIED', 'Изменён')], max_length=20, verbose_name='Действие')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='core.subscription')),
            ],
            options={
                'verbose_name': 'Лог абонемента',
                'verbose_name_plural': 'Логи абонемента',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['client', 'status'], name='core_subscri_client_i_...'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['subscription_type', 'status'], name='core_subscri_subscri_...'),
        ),
    ]
```

### 1.1.4 Регистрация в Admin

```python
# core/admin.py

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'client', 'course', 'subscription_type',
        'status', 'payment_status', 'start_date', 'end_date',
        'lessons_consumed', 'total_lessons', 'price', 'created_at'
    ]
    list_filter = [
        'subscription_type', 'status', 'payment_status',
        'start_date', 'end_date'
    ]
    search_fields = [
        'client__first_name', 'client__last_name',
        'course__name'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'final_price',
        'remaining_lessons', 'progress_percent'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('client', 'course', 'subscription_type')
        }),
        ('Условия', {
            'fields': (
                'total_lessons', 'start_date', 'end_date',
                'price', 'discount_percent', 'final_price'
            )
        }),
        ('Прогресс', {
            'fields': (
                'status', 'payment_status',
                'lessons_consumed', 'remaining_lessons', 'progress_percent'
            )
        }),
        ('Дополнительно', {
            'fields': ('notes', 'created_by')
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        
        if not change:
            SubscriptionLog.objects.create(
                subscription=obj,
                action='CREATED',
                created_by=request.user,
                description=f'Создан менеджером {request.user}'
            )


@admin.register(SubscriptionLog)
class SubscriptionLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'subscription', 'action', 'created_by', 'created_at']
    list_filter = ['action', 'created_at']
    readonly_fields = ['subscription', 'action', 'description', 'created_by', 'created_at']
```

---

## Шаг 1.2: Отчёт «Прогноз оплаты»

### 1.2.1 Описание
Отчёт показывает сумму, которую клиент должен заплатить за будущий период с учётом текущего остатка средств и запланированных занятий.

### 1.2.2 View-функция

```python
# payments/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from core.models import Client, Subscription, Lesson
from payments.models import Payment

def payment_forecast(request, client_id):
    """
    Отчёт «Прогноз оплаты»
    
    Возвращает:
    - Текущий баланс клиента
    - Запланированные занятия на период
    - Стоимость занятий
    - Рекомендуемая сумма к оплате
    """
    client = get_object_or_404(Client, id=client_id)
    
    # Период отчёта (по умолчанию следующий месяц)
    period_days = int(request.GET.get('period_days', 30))
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=period_days)
    
    # Активные абонементы клиента
    active_subscriptions = Subscription.objects.filter(
        client=client,
        status='ACTIVE'
    )
    
    # Запланированные занятия в период
    planned_lessons = Lesson.objects.filter(
        client=client,
        status='planned',
        start_time__gte=start_date,
        start_time__lt=end_date + timedelta(days=1)
    )
    
    # Расчёт стоимости
    forecast_data = {
        'client_id': client.id,
        'client_name': str(client),
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'days': period_days
        },
        'current_balance': client.balance,
        'bonuses': client.balance_bonus,
        'active_subscriptions': [],
        'planned_lessons': [],
        'total_forecast': 0,
        'recommended_payment': 0,
    }
    
    # Абонементы
    for sub in active_subscriptions:
        sub_data = {
            'id': sub.id,
            'name': str(sub),
            'type': sub.get_subscription_type_display(),
            'price': float(sub.final_price),
            'remaining_lessons': sub.remaining_lessons if sub.remaining_lessons != float('inf') else '∞',
        }
        forecast_data['active_subscriptions'].append(sub_data)
    
    # Планируемые занятия
    total_lessons_cost = 0
    for lesson in planned_lessons:
        lesson_data = {
            'id': lesson.id,
            'date': lesson.start_time.date().isoformat(),
            'time': lesson.start_time.time().isoformat(),
            'type': lesson.get_lesson_type_display(),
            'cost': float(lesson.course.base_price) if lesson.course else 0,
        }
        forecast_data['planned_lessons'].append(lesson_data)
        total_lessons_cost += lesson_data['cost']
    
    forecast_data['total_forecast'] = total_lessons_cost
    
    # Рекомендуемая сумма к оплате
    if client.balance + client.balance_bonus < total_lessons_cost:
        forecast_data['recommended_payment'] = total_lessons_cost - client.balance - client.balance_bonus
    else:
        forecast_data['recommended_payment'] = 0
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(forecast_data)
    
    return render(request, 'payments/forecast.html', forecast_data)
```

### 1.2.3 URL-маршрут

```python
# payments/urls.py

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # ... существующие маршруты ...
    path('client/<int:client_id>/forecast/', views.payment_forecast, name='payment_forecast'),
]
```

### 1.2.4 Шаблон отчёта

```html
<!-- templates/payments/forecast.html -->

{% extends 'base.html' %}

{% block title %}Прогноз оплаты — {{ client }}{% endblock %}

{% block content %}
<div class="forecast-page">
    <div class="page-header">
        <h1>Прогноз оплаты</h1>
        <p>{{ client.full_name }}</p>
    </div>
    
    <div class="forecast-summary glass-card">
        <div class="summary-item">
            <span class="label">Текущий баланс</span>
            <span class="value">{{ current_balance|floatformat:2 }} ₽</span>
        </div>
        <div class="summary-item">
            <span class="label">Бонусы</span>
            <span class="value">{{ bonuses|floatformat:2 }} б.</span>
        </div>
        <div class="summary-item highlight">
            <span class="label">Сумма к оплате</span>
            <span class="value">{{ recommended_payment|floatformat:2 }} ₽</span>
        </div>
    </div>
    
    <div class="forecast-period">
        <h2>Период: {{ period.start }} — {{ period.end }}</h2>
    </div>
    
    <div class="forecast-section">
        <h3>Активные абонементы</h3>
        {% if active_subscriptions %}
        <div class="subscription-list">
            {% for sub in active_subscriptions %}
            <div class="subscription-card glass-card">
                <div class="sub-header">
                    <strong>{{ sub.name }}</strong>
                    <span class="badge">{{ sub.type }}</span>
                </div>
                <div class="sub-details">
                    <span>Цена: {{ sub.price }} ₽</span>
                    <span>Осталось: {{ sub.remaining_lessons }}</span>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <p class="empty-state">Нет активных абонементов</p>
        {% endif %}
    </div>
    
    <div class="forecast-section">
        <h3>Запланированные занятия</h3>
        {% if planned_lessons %}
        <table class="lessons-table">
            <thead>
                <tr>
                    <th>Дата</th>
                    <th>Время</th>
                    <th>Тип</th>
                    <th>Стоимость</th>
                </tr>
            </thead>
            <tbody>
                {% for lesson in planned_lessons %}
                <tr>
                    <td>{{ lesson.date }}</td>
                    <td>{{ lesson.time }}</td>
                    <td>{{ lesson.type }}</td>
                    <td>{{ lesson.cost }} ₽</td>
                </tr>
                {% endfor %}
            </tbody>
            <tfoot>
                <tr class="total-row">
                    <td colspan="3"><strong>Итого</strong></td>
                    <td><strong>{{ total_forecast|floatformat:2 }} ₽</strong></td>
                </tr>
            </tfoot>
        </table>
        {% else %}
        <p class="empty-state">Нет запланированных занятий</p>
        {% endif %}
    </div>
    
    <div class="forecast-actions">
        <button class="btn btn-primary" onclick="window.print()">
            🖨️ Распечатать
        </button>
        <a href="{% url 'clients:client_detail' client.id %}" class="btn btn-secondary">
            ← Назад к клиенту
        </a>
    </div>
</div>

<style>
.forecast-page { padding: 20px; }
.page-header { margin-bottom: 20px; }
.forecast-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    padding: 20px;
    margin-bottom: 30px;
}
.summary-item { text-align: center; }
.summary-item .label { display: block; color: #888; font-size: 14px; }
.summary-item .value { display: block; font-size: 24px; font-weight: bold; }
.summary-item.highlight .value { color: #00dbe9; }
.forecast-section { margin-bottom: 30px; }
.subscription-list { display: grid; gap: 15px; }
.subscription-card { padding: 15px; }
.lessons-table { width: 100%; border-collapse: collapse; }
.lessons-table th, .lessons-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}
.total-row { background: rgba(0, 219, 233, 0.1); }
.forecast-actions { display: flex; gap: 15px; margin-top: 30px; }
</style>
{% endblock %}
```

---

## Шаг 1.3: Отчёт «Сверка взаиморасчетов»

### 1.3.1 Описание
Детальный отчёт по всем операциям с клиентом: платежи, списания, остаток.

### 1.3.2 View-функция

```python
# payments/views.py

def reconciliation_report(request, client_id):
    """
    Отчёт «Сверка взаиморасчетов»
    
    Показывает:
    - Все поступления (платежи)
    - Все списания (уроки, абонементы)
    - Остаток после каждой операции
    """
    client = get_object_or_404(Client, id=client_id)
    
    # Период
    start_date = request.GET.get('start_date', timezone.now().date() - timedelta(days=30))
    end_date = request.GET.get('end_date', timezone.now().date())
    
    # Входящий остаток (на начало периода)
    opening_balance = client.balance
    
    # Все операции
    operations = []
    
    # Платежи
    payments = Payment.objects.filter(
        client=client,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).order_by('created_at')
    
    for payment in payments:
        opening_balance += payment.amount
        operations.append({
            'date': payment.created_at.date().isoformat(),
            'type': 'PAYMENT',
            'description': f"Платёж #{payment.id} ({payment.get_payment_method_display()})",
            'payment': float(payment.amount),
            'deduction': 0,
            'balance': float(opening_balance),
        })
    
    # Списания за уроки
    lessons = Lesson.objects.filter(
        client=client,
        status='completed',
        start_time__gte=start_date,
        start_time__lte=end_date
    ).order_by('start_time')
    
    for lesson in lessons:
        cost = float(lesson.course.base_price) if lesson.course else 0
        opening_balance -= cost
        operations.append({
            'date': lesson.start_time.date().isoformat(),
            'type': 'LESSON',
            'description': f"Урок: {lesson.get_lesson_type_display()}",
            'payment': 0,
            'deduction': cost,
            'balance': float(opening_balance),
        })
    
    # Сортировка по дате
    operations.sort(key=lambda x: x['date'])
    
    # Итоги
    total_payments = sum(op['payment'] for op in operations)
    total_deductions = sum(op['deduction'] for op in operations)
    closing_balance = opening_balance
    
    report_data = {
        'client_id': client.id,
        'client_name': str(client),
        'period': {
            'start': start_date,
            'end': end_date,
        },
        'opening_balance': float(opening_balance - total_payments + total_deductions),
        'closing_balance': float(closing_balance),
        'total_payments': float(total_payments),
        'total_deductions': float(total_deductions),
        'operations': operations,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(report_data)
    
    return render(request, 'payments/reconciliation.html', report_data)
```

### 1.3.3 Шаблон

```html
<!-- templates/payments/reconciliation.html -->

{% extends 'base.html' %}

{% block title %}Сверка взаиморасчетов — {{ client }}{% endblock %}

{% block content %}
<div class="reconciliation-page">
    <div class="page-header">
        <h1>Сверка взаиморасчетов</h1>
        <p>{{ client.full_name }}</p>
    </div>
    
    <div class="period-selector">
        <label>Период:</label>
        <input type="date" id="start_date" value="{{ period.start }}">
        <input type="date" id="end_date" value="{{ period.end }}">
        <button class="btn btn-primary" onclick="updateReport()">Применить</button>
    </div>
    
    <div class="summary-cards">
        <div class="card">
            <h4>Входящий остаток</h4>
            <p class="value">{{ opening_balance|floatformat:2 }} ₽</p>
        </div>
        <div class="card">
            <h4>Всего поступлений</h4>
            <p class="value positive">+{{ total_payments|floatformat:2 }} ₽</p>
        </div>
        <div class="card">
            <h4>Всего списаний</h4>
            <p class="value negative">-{{ total_deductions|floatformat:2 }} ₽</p>
        </div>
        <div class="card highlight">
            <h4>Исходящий остаток</h4>
            <p class="value">{{ closing_balance|floatformat:2 }} ₽</p>
        </div>
    </div>
    
    <table class="reconciliation-table">
        <thead>
            <tr>
                <th>Дата</th>
                <th>Тип операции</th>
                <th>Описание</th>
                <th>Платежи</th>
                <th>Списание</th>
                <th>Остаток</th>
            </tr>
        </thead>
        <tbody>
            {% for op in operations %}
            <tr>
                <td>{{ op.date }}</td>
                <td>
                    {% if op.type == 'PAYMENT' %}
                    <span class="badge payment">Платёж</span>
                    {% else %}
                    <span class="badge deduction">Урок</span>
                    {% endif %}
                </td>
                <td>{{ op.description }}</td>
                <td class="amount payment">{% if op.payment > 0 %}+{{ op.payment|floatformat:2 }}{% endif %}</td>
                <td class="amount deduction">{% if op.deduction > 0 %}-{{ op.deduction|floatformat:2 }}{% endif %}</td>
                <td class="balance">{{ op.balance|floatformat:2 }}</td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="6" class="empty">Нет операций за период</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="actions">
        <button class="btn btn-primary" onclick="window.print()">🖨️ Распечатать</button>
        <button class="btn btn-secondary" onclick="exportExcel()">📊 Excel</button>
    </div>
</div>

<script>
function updateReport() {
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    window.location.href = `?start_date=${startDate}&end_date=${endDate}`;
}

function exportExcel() {
    // Реализовать экспорт в Excel
    alert('Экспорт в Excel будет добавлен в следующей версии');
}
</script>

<style>
.reconciliation-page { padding: 20px; }
.period-selector {
    display: flex;
    gap: 10px;
    align-items: center;
    margin-bottom: 20px;
}
.summary-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 30px;
}
.card {
    background: rgba(255,255,255,0.05);
    padding: 15px;
    border-radius: 8px;
    text-align: center;
}
.card.highlight { background: rgba(0, 219, 233, 0.1); }
.card h4 { font-size: 12px; color: #888; margin-bottom: 5px; }
.card .value { font-size: 20px; font-weight: bold; }
.card .value.positive { color: #10b981; }
.card .value.negative { color: #ef4444; }
.reconciliation-table { width: 100%; border-collapse: collapse; }
.reconciliation-table th, .reconciliation-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}
.badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.badge.payment { background: rgba(16, 185, 129, 0.2); color: #10b981; }
.badge.deduction { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.amount.payment { color: #10b981; }
.amount.deduction { color: #ef4444; }
.actions { margin-top: 20px; display: flex; gap: 10px; }
</style>
{% endblock %}
```

---

## Шаг 1.4: Тесты для моделей и отчётов

```python
# core/tests.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Client, Course, Subscription

User = get_user_model()

class SubscriptionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.client = Client.objects.create(
            first_name='Иван',
            last_name='Иванов',
            phone='+79991234567'
        )
        self.course = Course.objects.create(
            name='Базовый курс',
            base_price=5000,
            is_active=True
        )
    
    def test_create_monthly_subscription(self):
        """Тест создания месячного абонемента"""
        subscription = Subscription.objects.create(
            client=self.client,
            course=self.course,
            subscription_type='MONTHLY',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            price=10000,
            status='ACTIVE'
        )
        
        self.assertEqual(subscription.subscription_type, 'MONTHLY')
        self.assertEqual(subscription.final_price, 10000)
        self.assertEqual(subscription.remaining_lessons, float('inf'))
    
    def test_create_lesson_pack_subscription(self):
        """Тест создания абонемента-пакета"""
        subscription = Subscription.objects.create(
            client=self.client,
            course=self.course,
            subscription_type='LESSON_PACK',
            total_lessons=10,
            start_date=timezone.now().date(),
            price=8000,
            status='ACTIVE'
        )
        
        self.assertEqual(subscription.remaining_lessons, 10)
    
    def test_discount_calculation(self):
        """Тест расчёта скидки"""
        subscription = Subscription.objects.create(
            client=self.client,
            course=self.course,
            subscription_type='MONTHLY',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            price=10000,
            discount_percent=20,
            status='ACTIVE'
        )
        
        self.assertEqual(subscription.final_price, 8000)
    
    def test_consume_lesson(self):
        """Тест списания урока"""
        subscription = Subscription.objects.create(
            client=self.client,
            course=self.course,
            subscription_type='LESSON_PACK',
            total_lessons=10,
            start_date=timezone.now().date(),
            price=8000,
            status='ACTIVE'
        )
        
        subscription.consume_lesson()
        self.assertEqual(subscription.lessons_consumed, 1)
        
        # Потратить все уроки
        for _ in range(9):
            subscription.consume_lesson()
        
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, 'COMPLETED')
    
    def test_progress_calculation(self):
        """Тест расчёта прогресса"""
        subscription = Subscription.objects.create(
            client=self.client,
            course=self.course,
            subscription_type='LESSON_PACK',
            total_lessons=10,
            start_date=timezone.now().date(),
            price=8000,
            lessons_consumed=3,
            status='ACTIVE'
        )
        
        self.assertEqual(subscription.progress_percent, 30)


class PaymentForecastTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            first_name='Иван',
            last_name='Иванов',
            phone='+79991234567',
            balance=5000
        )
    
    def test_forecast_with_balance(self):
        """Тест прогноза при достаточном балансе"""
        # TODO: реализовать тест для view
        pass
    
    def test_forecast_insufficient_balance(self):
        """Тест прогноза при недостаточном балансе"""
        # TODO: реализовать тест для view
        pass
```

---

# 📊 Контрольные точки

| Шаг | Задачи | Срок | Статус |
|-----|--------|------|--------|
| 1.1 | Модель Абонементов + Admin | 3 дня | ⏳ |
| 1.2 | Отчёт «Прогноз оплаты» | 2 дня | ⏳ |
| 1.3 | Отчёт «Сверка взаиморасчетов» | 2 дня | ⏳ |
| 1.4 | Тесты | 1 день | ⏳ |
| **Итого Этап 1** | **4 подшага** | **8 дней** | ⏳ |

---

# 📝 Примечания

- Все даты хранятся в UTC
- Все денежные суммы — DecimalField с decimal_places=2
- Все API возвращают JSON для фронтенда
- Все критичные действия логируются
- Миграции должны быть протестированы на тестовой БД

---

# 🚀 Следующие этапы

После завершения Этапа 1 переходим к:
- Этап 2: Улучшенное расписание (регулярные уроки, табличный вид)
- Этап 3: Личный кабинет и онлайн-оплата
- Этап 4: Аналитика и дашборды
- Этап 5: Интеграции и автоматизация
