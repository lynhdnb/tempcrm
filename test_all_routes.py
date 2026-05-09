#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Комплексная проверка всех маршрутов и импортов
Запуск: python test_all_routes.py
"""
import os
import sys
import re

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.contrib.auth import get_user_model
from core.models import Client, Course, CourseCategory, Enrollment
from lessons.models import Lesson, LessonType
from payments.models import Payment
from interactions.models import Interaction
from tasks.models import Task

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_status(status, message):
    if status == 'OK':
        print(f"{GREEN}OK{RESET} {message}")
    elif status == 'WARN':
        print(f"{YELLOW}WARN{RESET} {message}")
    else:
        print(f"{RED}ERROR{RESET} {message}")

def test_imports():
    print("\n" + "="*60)
    print("1. ПРОВЕРКА ИМПОРТОВ")
    print("="*60)
    
    errors = []
    try:
        from core.views import client_list, client_detail, client_create, client_update, client_delete
        print_status('OK', 'Все view функции импортированы успешно')
    except ImportError as e:
        print_status('ERROR', f'Ошибка импорта views: {e}')
        errors.append(str(e))
    
    return len(errors) == 0

def test_urls():
    print("\n" + "="*60)
    print("2. ПРОВЕРКА URL МАРШРУТОВ")
    print("="*60)
    
    urls_to_test = [
        ('core:dashboard', []),
        ('core:client_list', []),
        ('core:client_create', []),
        ('core:client_detail', [1]),
        ('core:client_update', [1]),
        ('core:client_delete', [1]),
        ('core:courses_list', []),
        ('core:enrollments_list', []),
        ('core:enrollment_detail', [1]),
        ('core:payments_list', []),
        ('core:tasks_list', []),
        ('core:schedule', []),
    ]
    
    errors = []
    for url_name, args in urls_to_test:
        try:
            url = reverse(url_name, args=args)
            print_status('OK', f'{url_name:30} → {url}')
        except NoReverseMatch as e:
            print_status('ERROR', f'{url_name:30} → ОШИБКА: {e}')
            errors.append(str(e))
    
    return len(errors) == 0

def test_redirects():
    print("\n" + "="*60)
    print("3. ПРОВЕРКА REDIRECT В VIEW ФУНКЦИЯХ")
    print("="*60)
    
    errors = []
    
    with open('core/views.py', 'r', encoding='utf-8') as f:
        views_content = f.read()
    
    redirect_pattern = r"redirect\(['\"]core:([^'\"]+)['\"]\)"
    redirects = re.findall(redirect_pattern, views_content)
    
    print(f"Найдено {len(redirects)} редиректов")
    
    for url_name in set(redirects):
        try:
            url = reverse(f'core:{url_name}')
            print_status('OK', f'redirect(\'core:{url_name}\') → {url}')
        except NoReverseMatch as e:
            print_status('ERROR', f'redirect(\'core:{url_name}\') → ОШИБКА: {e}')
            errors.append(str(e))
    
    return len(errors) == 0

def test_models():
    print("\n" + "="*60)
    print("4. ПРОВЕРКА РАБОТЫ МОДЕЛЕЙ")
    print("="*60)
    
    errors = []
    
    try:
        print_status('OK', f'Client.objects.count() = {Client.objects.count()}')
    except Exception as e:
        print_status('ERROR', f'Client.objects: {e}')
        errors.append(str(e))
    
    try:
        print_status('OK', f'Course.objects.count() = {Course.objects.count()}')
    except Exception as e:
        print_status('ERROR', f'Course.objects: {e}')
        errors.append(str(e))
    
    return len(errors) == 0

def main():
    print("\n" + "="*60)
    print("КОМПЛЕКСНАЯ ПРОВЕРКА DJ CRM")
    print("="*60)
    
    results = [
        ('Импорты', test_imports()),
        ('URL маршруты', test_urls()),
        ('Redirections', test_redirects()),
        ('Модели', test_models()),
    ]
    
    print("\n" + "="*60)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = f"{GREEN}ПРОШЛО{RESET}" if passed else f"{RED}НЕ ПРОШЛО{RESET}"
        print(f"{name:20} → {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print(f"{GREEN}ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!{RESET}")
        return 0
    else:
        print(f"{RED}ЕСТЬ ОШИБКИ!{RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())