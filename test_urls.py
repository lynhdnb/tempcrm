#!/usr/bin/env python
"""
Тестирование URL маршрутов DJ CRM v2
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import reverse, NoReverseMatch

# Список всех URL для тестирования
urls = [
    # Дашборд и авторизация
    {'name': 'core:dashboard', 'args': [], 'desc': 'Главный дашборд'},
    {'name': 'core:login', 'args': [], 'desc': 'Страница входа'},
    {'name': 'core:logout', 'args': [], 'desc': 'Выход из системы'},
    
    # Клиенты
    {'name': 'core:client_list', 'args': [], 'desc': 'Список клиентов'},
    {'name': 'core:client_create', 'args': [], 'desc': 'Создание клиента'},
    
    # Курсы
    {'name': 'core:courses_list', 'args': [], 'desc': 'Список курсов'},
    {'name': 'core:course_create', 'args': [], 'desc': 'Создание курса'},
    {'name': 'core:enroll_client', 'args': [1], 'desc': 'Запись на курс'},
    
    # Записи
    {'name': 'core:enrollments_list', 'args': [], 'desc': 'Список записей'},
    {'name': 'core:enrollment_detail', 'args': [1], 'desc': 'Детали записи'},
    
    # Платежи
    {'name': 'core:payments_list', 'args': [], 'desc': 'Список платежей'},
    
    # Задачи
    {'name': 'core:tasks_list', 'args': [], 'desc': 'Список задач'},
    
    # Расписание
    {'name': 'core:schedule', 'args': [], 'desc': 'Расписание'},
    
    # Личный кабинет студента
    {'name': 'core:student_dashboard', 'args': [], 'desc': 'Личный кабинет студента'},
    {'name': 'core:student_lessons', 'args': [], 'desc': 'Занятия студента'},
    {'name': 'core:student_payments', 'args': [], 'desc': 'Платежи студента'},
    {'name': 'core:student_progress', 'args': [1], 'desc': 'Прогресс студента'},
    
    # Дашборд преподавателя
    {'name': 'core:teacher_dashboard', 'args': [], 'desc': 'Дашборд преподавателя'},
    {'name': 'core:teacher_schedule', 'args': [], 'desc': 'Расписание преподавателя'},
    {'name': 'core:teacher_students', 'args': [], 'desc': 'Студенты преподавателя'},
    {'name': 'core:teacher_lesson_mark', 'args': [1], 'desc': 'Отметить занятие'},
    
    # Панель менеджера
    {'name': 'core:manager_dashboard', 'args': [], 'desc': 'Дашборд менеджера'},
    {'name': 'core:manager_clients_quick', 'args': [], 'desc': 'Клиенты менеджера'},
    {'name': 'core:manager_enrollments_quick', 'args': [], 'desc': 'Записи менеджера'},
    {'name': 'core:manager_payments_quick', 'args': [], 'desc': 'Платежи менеджера'},
]

print("=" * 80)
print("ТЕСТИРОВАНИЕ URL МАРШРУТОВ DJ CRM v2")
print("=" * 80)
print()

passed = 0
failed = 0
errors = []

for item in urls:
    name = item['name']
    args = item['args']
    desc = item['desc']
    
    try:
        url = reverse(name, args=args)
        print(f"[OK] {desc:40} -> {url}")
        passed += 1
    except NoReverseMatch as e:
        print(f"[FAIL] {desc:40} -> {str(e)[:50]}")
        failed += 1
        errors.append(f"{desc}: {name} - {str(e)}")

print()
print("=" * 80)
print(f"РЕЗУЛЬТАТЫ: {passed} пройдено, {failed} не пройдено")
print("=" * 80)

if errors:
    print("\nОшибки:")
    for error in errors:
        print(f"  - {error}")

sys.exit(0 if failed == 0 else 1)
