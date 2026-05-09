# Quick Start - DJ CRM v2

## 🚀 Быстрый запуск (5 минут)

### 1. Установка зависимостей

```bash
pip install django psycopg2-binary django-environ
```

### 2. Настройка окружения

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=django-insecure-dev-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Для PostgreSQL (опционально)
DB_ENGINE=postgresql
DB_NAME=djcrm
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

**Примечание:** Если PostgreSQL не настроен, система автоматически переключится на SQLite.

### 3. Применение миграций

```bash
python manage.py migrate
```

### 4. Инициализация ролей

```bash
python manage.py init_roles
```

Это создаст 5 базовых ролей:
- Владелец (OWNER)
- Администратор (ADMIN)
- Менеджер (MANAGER)
- Преподаватель (TEACHER)
- Ученик (STUDENT)

### 5. Создание суперпользователя

```bash
python manage.py createsuperuser
```

Или через Python:
```bash
$env:DJANGO_SETTINGS_MODULE='config.settings'; python -c "import django; django.setup(); from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"
```

**Логин:** `admin`  
**Пароль:** `admin123`

### 6. Запуск сервера

```bash
python manage.py runserver
```

Откройте в браузере:
- **Дашборд:** http://127.0.0.1:8000/dashboard/
- **Админка:** http://127.0.0.1:8000/admin/

---

## 📋 Проверка работы

### 1. Проверка миграций

```bash
python manage.py showmigrations
```

Все миграции должны быть отмечены `[X]`.

### 2. Проверка ролей

```bash
python manage.py shell
>>> from core.models import Role
>>> Role.objects.all()
<QuerySet [<Role: Владелец (OWNER)>, <Role: Администратор (ADMIN)>, ...]>
```

### 3. Проверка админки

Зайдите в http://127.0.0.1:8000/admin/ под суперпользователем и убедитесь, что все модели доступны:
- **Core:** Client, ContactPerson, EmployeeProfile, Role, RoleAssignment
- **Interactions:** InteractionType, Interaction, Comment
- **Lessons:** LessonType, Lesson, Attendance
- **Payments:** PaymentMethod, PaymentPackage, Contract, Payment, Invoice
- **Tasks:** Task

---

## 📁 Структура проекта

```
DJ_CRM_v2/
├── config/              # Настройки проекта
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                # Основные данные
│   ├── models.py        # Client, Role, EmployeeProfile
│   ├── signals.py       # Автоматические триггеры
│   ├── permissions.py   # Права доступа
│   ├── middleware.py    # Проверка прав
│   └── admin.py         # Регистрация в админке
├── interactions/        # Взаимодействия с клиентами
├── lessons/             # Занятия и расписание
├── payments/            # Финансы и платежи
├── tasks/               # Задачи
├── manage.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
└── QUICKSTART.md
```

---

## 🔧 Полезные команды

### Очистка базы данных

```bash
# Удалить базу данных и начать заново
Remove-Item -Path db.sqlite3 -Force
python manage.py migrate
python manage.py init_roles
```

### Создание тестовых данных

```bash
python manage.py shell
>>> from core.models import Client, Role
>>> Client.objects.create(first_name='Иван', last_name='Иванов', phone='+79001234567')
>>> Role.objects.filter(code='OWNER').first()
```

### Проверка логов

```bash
# При запуске сервера
python manage.py runserver --verbosity 2
```

---

## 🆘 Решение проблем

### Проблема: Ошибка подключения к PostgreSQL

**Решение:** Убедитесь, что PostgreSQL запущен, или удалите настройки PostgreSQL из `.env` для использования SQLite.

### Проблема: Ошибка кодировки в Windows

**Решение:** Используйте PowerShell с UTF-8 кодировкой:
```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
```

### Проблема: Таблицы не созданы

**Решение:**
```bash
python manage.py migrate --run-syncdb
```

### Проблема: Роль не назначена пользователю

**Решение:** Через админку:
1. Зайдите в `/admin/`
2. Перейдите в `Role assignments`
3. Создайте новое назначение роли для пользователя

---

## 📞 Следующие шаги

1. **Настроить систему ролей** - назначьте роли пользователям
2. **Создать типы занятий** - в админке `lessons.LessonType`
3. **Добавить способы оплаты** - в админке `payments.PaymentMethod`
4. **Настроить email** - для уведомлений о платежах и задачах
5. **Развернуть на продакшен** - следуйте инструкции в `README.md`

---

**Готово!** Проект DJ CRM v2 запущен и готов к использованию.
