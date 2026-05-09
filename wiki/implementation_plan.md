# План реализации улучшений DJ CRM v2

## 🎯 Этап 1: Абонементы и финансовая аналитика (2-3 недели)

### 1.1 Модель Абонементов
```python
# core/models.py — добавить
class Subscription(models.Model):
    """Абонементы — помесечные и поурочные"""
    TYPE_CHOICES = [
        ('MONTHLY', 'Помесячный'),
        ('LESSON_PACK', 'Пакет уроков'),
    ]
    
    client = ForeignKey(Client)
    course = ForeignKey(Course)
    type = CharField(choices=TYPE_CHOICES)
    lessons_count = PositiveIntegerField()  # для пакетов
    price = DecimalField()
    start_date = DateField()
    end_date = DateField()  # для месячных
    used_lessons = PositiveIntegerField(default=0)
    status = CharField(choices=[('ACTIVE', 'Активен'), ('EXPIRED', 'Истёк'), ('PAUSED', 'Пауза')])
```

### 1.2 Отчёт «Прогноз оплаты»
```python
# payments/views.py
def forecast_payment(request, client_id):
    """Расчёт суммы к оплате за будущий период"""
    # Логика: запланированные занятия × цена абонемента
    pass

# payments/urls.py
path('client/<int:client_id>/forecast/', forecast_payment, name='payment_forecast')
```

### 1.3 Отчёт «Сверка взаиморасчетов»
```python
# payments/views.py
def reconciliation_report(request, client_id):
    """Детальный анализ платежей и списаний за период"""
    # Таблица: Дата | Тип операции | Платежи | Списание | Остаток
    pass
```

**Задачи:**
- [ ] Создать миграцию для модели Subscription
- [ ] Admin интерфейс для управления абонементом
- [ ] API для создания/редактирования абонементов
- [ ] Шаблон списка абонементов клиента
- [ ] Шаблон отчёта «Прогноз оплаты»
- [ ] Шаблон отчёта «Сверка взаиморасчетов»
- [ ] Тесты для расчётов

---

## 🎯 Этап 2: Улучшенное расписание (2-3 недели)

### 2.1 Табличное отображение уроков
```python
# lessons/views.py
def lesson_list_table(request):
    """Список уроков в табличном виде с фильтрами"""
    # Поля: ID | Дата | Ученик | Преподаватель | Аудитория | Статус | Участники
    pass
```

### 2.2 Регулярное расписание
```python
# lessons/models.py
class RegularLessonSchedule(models.Model):
    """Регулярное расписание — периодические занятия"""
    client = ForeignKey(Client)
    course = ForeignKey(Course)
    teacher = ForeignKey(EmployeeProfile)
    room = ForeignKey(Room, null=True)
    
    start_date = DateField()
    end_date = DateField()
    weekday = SmallIntegerField()  # 0=Пн, 1=Вт...
    start_time = TimeField()
    duration_minutes = PositiveIntegerField(default=60)
    
    type = CharField(choices=[('INDIVIDUAL', 'Индивидуальный'), ('GROUP', 'Групповой')])
    status = CharField(choices=[('ACTIVE', 'Активно'), ('ARCHIVED', 'Архив')])
```

### 2.3 График работы педагогов
```python
# lessons/views.py
def teacher_schedule_view(request):
    """Визуализация рабочего графика и свободных окон"""
    # Цветовая кодировка: зелёный=свободно, карточка=занято, розовый=вне графика
    pass
```

### 2.4 Массовая отмена уроков
```python
# lessons/views.py
@permission_required('lessons.cancel_lessons')
def bulk_cancel_lessons(request):
    """Массовая отмена запланированных уроков с комментарием"""
    # Проверка закрытого периода
    # Протокол выполнения операции
    pass
```

**Задачи:**
- [ ] Миграция для RegularLessonSchedule
- [ ] Табличный вид уроков с настройкой полей
- [ ] Форма создания регулярного расписания
- [ ] Генерация уроков из регулярного расписания
- [ ] График работы педагогов (визуализация)
- [ ] Массовая отмена с протоколом
- [ ] Экспорт посещаемости в Excel
- [ ] API для регулярного расписания

---

## 🎯 Этап 3: Личный кабинет и оплата (3-4 недели)

### 3.1 Оплата счетов онлайн
```python
# payments/views.py
def online_payment(request, payment_id):
    """Оплата счета через эквайринг/банк"""
    # Интеграция с CloudPayments / ЮKassa / Тинькофф
    pass

# payments/models.py
class Payment(models.Model):
    # Добавить поля
    payment_url = URLField()  # ссылка для оплаты
    payment_status = CharField(choices=[('PENDING', 'Ожидает'), ('PAID', 'Оплачено'), ('FAILED', 'Ошибка')])
    transaction_id = CharField(max_length=100, blank=True)
```

### 3.2 Улучшенный кабинет ученика
```python
# students/views.py
def student_dashboard(request):
    """Главная страница кабинета ученика"""
    # Блоки: следующее занятие, баланс, домашка, бонусы
    pass
```

### 3.3 Бонусная система
```python
# core/models.py
class BonusTransaction(models.Model):
    """История начисления и списания бонусов"""
    client = ForeignKey(Client)
    amount = DecimalField()  # положительное=начисление, отрицательное=списание
    reason = CharField()  # причина
    created_at = DateTimeField(auto_now_add=True)
```

**Задачи:**
- [ ] Интеграция с эквайрингом (ЮKassa / CloudPayments)
- [ ] Шаблон оплаты счета
- [ ] Webhook для обработки платежей
- [ ] Улучшенный дашборд ученика
- [ ] Бонусная система (начисление/списание)
- [ ] История бонусов в кабинете
- [ ] API для мобильного приложения

---

## 🎯 Этап 4: Аналитика и дашборды (2-3 недели)

### 4.1 Метрики бизнеса
```python
# analytics/views.py
def business_metrics(request):
    """CAC, LTV, ARPU, Удержание, Отток"""
    metrics = {
        'cac': calculate_cac(),  # стоимость привлечения
        'ltv': calculate_ltv(),  # пожизненная ценность
        'arpu': calculate_arpu(),  # средняя выручка на пользователя
        'retention': calculate_retention(),  # удержание
        'churn': calculate_churn(),  # отток
    }
    return metrics
```

### 4.2 Кастомизируемый дашборд
```python
# dashboard/models.py
class UserDashboard(models.Model):
    """Настройка дашборда пользователем"""
    user = ForeignKey(User)
    widgets = JSONField()  # список виджетов и их конфигурация
    layout = JSONField()  # раскладка
    is_public = BooleanField(default=False)  # публичный или приватный
```

**Задачи:**
- [ ] Калькулятор метрик (CAC, LTV, ARPU, Retention, Churn)
- [ ] Графики в дашборде (Chart.js или ApexCharts)
- [ ] Настройка виджетов дашборда
- [ ] Сохранение настроек дашборда
- [ ] Публичные/приватные дашборды
- [ ] Экспорт отчётов в PDF

---

## 🎯 Этап 5: Интеграции и автоматизация (3-4 недели)

### 5.1 Триггеры и уведомления
```python
# automation/models.py
class Trigger(models.Model):
    """Автоматические действия по событиям"""
    event_type = CharField(choices=[
        ('LESSON_SCHEDULED', 'Урок запланирован'),
        ('LESSON_COMPLETED', 'Урок проведён'),
        ('PAYMENT_DUE', 'Платеж должен быть'),
        ('CLIENT_SILENT', 'Клиент молчит'),
    ])
    action_type = CharField(choices=[
        ('EMAIL', 'Отправить email'),
        ('SMS', 'Отправить SMS'),
        ('NOTIFICATION', 'Внутреннее уведомление'),
        ('TELEGRAM', 'Telegram-бот'),
    ])
    template = TextField()  # шаблон сообщения
    delay_minutes = PositiveIntegerField(default=0)  # задержка
```

### 5.2 Чат в CRM
```python
# interactions/models.py
class ChatMessage(models.Model):
    """Сообщения в чате между пользователями"""
    sender = ForeignKey(User, related_name='sent_messages')
    recipient = ForeignKey(User, related_name='received_messages')
    content = TextField()
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

### 5.3 Интеграции
- Телефония (Twilio, Zadarma)
- SMS-рассылки
- Telegram-бот
- Онлайн-кассы (АТОЛ, Штрих-М)

**Задачи:**
- [ ] Система триггеров и событий
- [ ] Шаблоны уведомлений
- [ ] Чат между пользователями
- [ ] Интеграция с Telegram-ботом
- [ ] Интеграция с эквайрингом
- [ ] API для сторонних сервисов

---

## 📊 Оценка времени

| Этап | Задачи | Сложность | Время |
|------|--------|-----------|-------|
| 1. Абонементы | 7 задач | Medium | 2-3 недели |
| 2. Расписание | 8 задач | High | 2-3 недели |
| 3. Кабинет + оплата | 7 задач | High | 3-4 недели |
| 4. Аналитика | 6 задач | Medium | 2-3 недели |
| 5. Интеграции | 6 задач | Very High | 3-4 недели |

**Итого:** 12-17 недель (3-4 месяца)

---

## 🚀 MVP (Минимально жизнеспособный продукт)

Если нужно быстрее выйти на рынок, приоритет:

1. **Абонементы** (1.1) — 1 неделя
2. **Регулярное расписание** (2.2) — 1 неделя
3. **Табличный вид уроков** (2.1) — 3 дня
4. **Улучшенный кабинет** (3.2) — 1 неделя

**MVP срок:** 3-4 недели

---

## 📝 Примечания

- Все модели должны иметь `created_at`, `updated_at`
- Все API должны быть защищены авторизацией
- Все критичные операции должны логироваться
- Нужны unit-тесты для расчётов (абонементы, бонусы, метрики)
- Интеграции — через очереди задач (Celery)
