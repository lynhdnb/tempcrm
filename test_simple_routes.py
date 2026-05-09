#!/usr/bin/env python
"""
Простое тестирование основных маршрутов DJ CRM
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from core.models import Client, Course, CourseCategory, Enrollment, EmployeeProfile
from lessons.models import Lesson, LessonType
from payments.models import Payment
from tasks.models import Task

User = get_user_model()

def test_routes():
    client = Client()
    passed = 0
    failed = 0
    
    # Создаём тестового пользователя
    test_user, _ = User.objects.get_or_create(
        username='test_admin',
        defaults={'is_staff': True, 'is_superuser': True}
    )
    test_user.set_password('testpass123')
    test_user.save()
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ МАРШРУТОВ DJ CRM")
    print("="*60)
    
    # Логин
    client.force_login(test_user)
    
    routes = [
        # Дашборд
        ('/dashboard/', 200),
        ('/manager/', 200),
        
        # Клиенты
        ('/clients/', 200),
        
        # Курсы
        ('/courses/', 200),
        
        # Записи
        ('/enrollments/', 200),
        
        # Платежи
        ('/payments/', 200),
        
        # Задачи
        ('/tasks/', 200),
        
        # Расписание
        ('/schedule/', 200),
        
        # Панели
        ('/manager/clients/', 200),
        ('/manager/enrollments/', 200),
        ('/manager/payments/', 200),
        
        # Преподаватель
        ('/teacher/', 200),
        ('/teacher/schedule/', 200),
        ('/teacher/students/', 200),
        
        # Студент
        ('/student/', 200),
        ('/student/lessons/', 200),
        ('/student/payments/', 200),
    ]
    
    for url, expected in routes:
        try:
            response = client.get(url)
            if response.status_code == expected:
                print(f"[OK] {url} -> {response.status_code}")
                passed += 1
            else:
                print(f"[FAIL] {url} -> {response.status_code} (expected {expected})")
                failed += 1
        except Exception as e:
            print(f"[ERROR] {url} -> {str(e)[:80]}")
            failed += 1
    
    print("\n" + "="*60)
    print("ИТОГИ")
    print("="*60)
    print(f"Пройдено: {passed}")
    print(f"Не пройдено: {failed}")
    print(f"Всего: {passed + failed}")
    
    return failed == 0

if __name__ == '__main__':
    success = test_routes()
    sys.exit(0 if success else 1)