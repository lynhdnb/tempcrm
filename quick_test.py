import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first()

if not admin:
    print("No admin user found!")
    exit(1)

c = Client()
c.force_login(admin)

urls = [
    ('/', 'Главная (редирект)'),
    ('/dashboard/', 'Дашборд'),
    ('/login/', 'Страница входа'),
    ('/clients/', 'Список клиентов'),
    ('/clients/create/', 'Создание клиента'),
    ('/courses/', 'Список курсов'),
    ('/courses/create/', 'Создание курса'),
    ('/enrollments/', 'Список записей'),
    ('/payments/', 'Список платежей'),
    ('/tasks/', 'Список задач'),
    ('/schedule/', 'Расписание'),
]

print("=" * 70)
print("ТЕСТИРОВАНИЕ URL МАРШРУТОВ (НОВАЯ СТРУКТУРА)")
print("=" * 70)

passed = 0
failed = 0

for url, desc in urls:
    try:
        response = c.get(url)
        status = response.status_code
        if status == 200 or status == 302:
            print(f"[OK]   {desc:30} {url:35} {status}")
            passed += 1
        else:
            print(f"[FAIL] {desc:30} {url:35} {status}")
            failed += 1
    except Exception as e:
        print(f"[ERROR] {desc:30} {url:35} {str(e)[:30]}")
        failed += 1

print("=" * 70)
print(f"РЕЗУЛЬТАТ: {passed} пройдено, {failed} не пройдено")
print("=" * 70)

if failed == 0:
    print("\n[SUCCESS] Все URL работают корректно!")
else:
    print(f"\n[WARNING] {failed} URL требуют внимания")
