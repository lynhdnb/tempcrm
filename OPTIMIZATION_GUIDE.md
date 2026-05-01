# Оптимизация ERP-системы музыкальной школы

## Что уже сделано:

### 1. Индексы в базе данных
Добавлены индексы (`db_index=True`) для ускорения поиска по часто используемым полям:

**Модель Client:**
- `phone` — поиск по телефону
- `email` — поиск по email  
- `status` — фильтрация по статусу клиента
- `created_at` — сортировка по дате создания

**Модель Interaction:**
- `client` — связь с клиентом
- `interaction_type` — тип взаимодействия (задача, звонок, комментарий)

**Модель Lesson:**
- `client` — связь с клиентом
- `teacher` — связь с преподавателем
- `room` — связь с кабинетом
- `enrollment` — связь с абонементом
- `lesson_type` — тип занятия
- `status` — статус занятия
- `start_time` — время начала (для расписания)

**Модель Enrollment:**
- `client` — связь с клиентом
- `product` — связь с продуктом
- `status` — статус записи

**Модель Payment:**
- `enrollment` — связь с записью
- `is_paid` — статус оплаты

### 2. Оптимизация запросов (select_related)
В представлениях добавлено предварительное соединение таблиц:

**clients/views.py:**
- В `client_list()` — загрузка менеджера клиента
- В `client_detail()` — загрузка авторов и исполнителей задач

Это устраняет проблему N+1 запросов, когда для каждого объекта делался отдельный запрос к базе.

---

## Что нужно сделать дальше:

### 1. Применить миграции
После добавления индексов нужно применить миграции на боевой базе:

```bash
python manage.py migrate
```

⚠️ **Важно:** На большой базе создание индексов может занять время. Лучше делать это в период низкой нагрузки.

---

### 2. Настроить кэширование (Redis)

**Установить Redis:**
```bash
sudo apt install redis-server
pip install django-redis
```

**Добавить в settings.py:**
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

**Что кэшировать:**
- Списки клиентов (особенно с фильтрами)
- Расписание занятий
- Статистику и отчёты
- Часто используемые справочники

---

### 3. Внедрить асинхронные задачи (Celery)

**Установить:**
```bash
pip install celery redis
```

**Какие задачи вынести в фон:**
- Отправка email уведомлений
- Создание платежей рассрочки
- Проверка дедлайнов задач
- Обновление статусов занятий
- Генерация отчётов

**Пример настройки tasks.py:**
```python
from celery import shared_task

@shared_task
def send_email_notification(user_id, message):
    # Отправка email без блокировки основного процесса
    pass

@shared_task
def check_task_deadlines():
    # Проверка просроченных задач
    pass
```

---

### 4. Добавить пагинацию

В списках с большим количеством записей добавить постраничную навигацию:

**clients/views.py:**
```python
from django.core.paginator import Paginator

def client_list(request):
    clients = Client.objects.all()
    paginator = Paginator(clients, 50)  # 50 клиентов на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'clients/client_list.html', {'page_obj': page_obj})
```

---

### 5. Оптимизировать метод get_lesson_number()

Текущая реализация делает несколько запросов к базе. Можно улучшить через агрегацию:

```python
from django.db.models import Count, Q

def get_lesson_number(self):
    if not self.enrollment:
        return None
    
    base_query = Lesson.objects.filter(
        client=self.client,
        enrollment=self.enrollment,
        lesson_type=self.lesson_type
    )
    
    completed = base_query.filter(
        status__in=['completed', 'no_show'],
        start_time__lt=self.start_time
    ).count()
    
    if self.status in ['scheduled', 'confirmed', 'in_progress']:
        scheduled_before = base_query.filter(
            status__in=['scheduled', 'confirmed', 'in_progress'],
            start_time__lt=self.start_time
        ).count()
        return completed + scheduled_before + 1
    
    return completed + 1
```

---

### 6. Мониторинг производительности

**Установить Django Debug Toolbar:**
```bash
pip install django-debug-toolbar
```

Добавить в `INSTALLED_APPS` и настроить middleware для отслеживания:
- Количества SQL-запросов
- Времени выполнения запросов
- Проблемных мест в коде

---

## Ожидаемый результат:

✅ Поиск клиентов по телефону/email станет мгновенным  
✅ Фильтрация по статусам будет работать быстрее  
✅ Страница клиента загрузится в 3-5 раз быстрее  
✅ Исчезнут "подвисания" при работе с расписанием  
✅ Сервер будет меньше нагружен при пиковых нагрузках  

---

## Приоритеты внедрения:

1. **Срочно** — Применить миграции с индексами
2. **Высокий** — Настроить кэширование Redis
3. **Средний** — Внедрить Celery для фоновых задач
4. **Низкий** — Добавить пагинацию и мониторинг

---

## Контакты для вопросов

По техническим вопросам оптимизации обращайтесь к разработчику, который внёс эти изменения.
