#!/usr/bin/env python
"""
Комплексное тестирование всех маршрутов и функциональности DJ CRM
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse

# Модели
from core.models import Client, Course, CourseCategory, Enrollment, EmployeeProfile, Role, RoleAssignment
from lessons.models import Lesson, LessonType
from payments.models import Payment, PaymentMethod
from tasks.models import Task
from interactions.models import Interaction, Notification

class CRMTester:
    def __init__(self):
        self.client = Client()
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # Создаём тестового пользователя
        self.test_user, _ = User.objects.get_or_create(
            username='test_admin',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        self.test_user.set_password('testpass123')
        self.test_user.save()
        
        self.test_teacher, _ = User.objects.get_or_create(
            username='test_teacher',
            defaults={'is_staff': True}
        )
        self.test_teacher.set_password('testpass123')
        self.test_teacher.save()
        
        self.test_student, _ = User.objects.get_or_create(
            username='test_student',
            defaults={'is_staff': False}
        )
        self.test_student.set_password('testpass123')
        self.test_student.save()
    
    def test_route(self, url, method='get', expected_status=200, data=None):
        """Тестирование одного маршрута"""
        try:
            if method == 'get':
                response = self.client.get(url)
            elif method == 'post':
                response = self.client.post(url, data or {})
            else:
                response = self.client.get(url)
            
            if response.status_code == expected_status:
                print(f"  [OK] {url} ({response.status_code})")
                self.results['passed'] += 1
                return True
            else:
                print(f"  [FAIL] {url} (Ожидалось {expected_status}, получено {response.status_code})")
                self.results['failed'] += 1
                self.results['errors'].append(f"{url}: статус {response.status_code}")
                return False
        except Exception as e:
            print(f"  [ERROR] {url}: {str(e)[:100]}")
            self.results['failed'] += 1
            self.results['errors'].append(f"{url}: {str(e)}")
            return False
    
    def test_authentication(self):
        """Тестирование авторизации"""
        print("\n" + "="*60)
        print("1. АВТОРИЗАЦИЯ")
        print("="*60)
        
        # Страница входа
        self.test_route('/login/', expected_status=200)
        
        # Логин через session
        self.client.login(username='test_admin', password='testpass123')
        
        # Дашборд (требуется авторизация)
        self.test_route('/dashboard/', expected_status=200)
        
        # Выход
        self.test_route('/logout/', expected_status=302)
        
        # Проверка, что без логина нельзя войти
        self.client.logout()
        response = self.client.get('/dashboard/')
        if response.status_code == 302:
            print(f"  [OK] /dashboard/ требует авторизации (302)")
            self.results['passed'] += 1
        else:
            print(f"  [FAIL] /dashboard/ не требует авторизации ({response.status_code})")
            self.results['failed'] += 1
    
    def test_dashboard_routes(self):
        """Тестирование дашбордов"""
        print("\n" + "="*60)
        print("2. ДАШБОРДЫ")
        print("="*60)
        
        self.client.login(username='test_admin', password='testpass123')
        
        # Главный дашборд
        self.test_route('/dashboard/', expected_status=200)
        
        # Дашборд менеджера
        self.test_route('/manager/', expected_status=200)
        
        # Дашборд преподавателя
        self.test_teacher_profile, _ = EmployeeProfile.objects.get_or_create(
            user=self.test_teacher,
            defaults={'hire_date': date.today()}
        )
        self.client.login(username='test_teacher', password='testpass123')
        self.test_route('/teacher/', expected_status=200)
        
        # Дашборд студента
        self.client.login(username='test_student', password='testpass123')
        self.test_route('/student/', expected_status=200)
        
    def test_client_routes(self):
        """Тестирование работы с клиентами"""
        print("\n" + "="*60)
        print("3. КЛИЕНТЫ")
        print("="*60)
        
        self.client.login(username='test_admin', password='testpass123')
        
        # Список клиентов
        self.test_route('/clients/', expected_status=200)
        
        # Создаём тестового клиента
        test_client, _ = Client.objects.get_or_create(
            phone='+79991112233',
            defaults={
                'first_name': 'Тестовый',
                'last_name': 'Клиент',
                'email': 'testclient@example.com',
                'status': 'POTENTIAL'
            }
        )
        
        # Детали клиента
        self.test_route(f'/clients/{test_client.pk}/', expected_status=200)
        
        # Форма создания клиента
        self.test_route('/clients/create/', expected_status=200)
        
        # Создание клиента через POST
        response = self.client.post('/clients/create/', {
            'first_name': 'Новый',
            'last_name': 'Клиент',
            'phone': '+79990001111',
            'email': 'new@example.com'
        })
        if response.status_code == 302:  # Редирект после успешного создания
            print(f"  ✓ /clients/create/ POST (302 - создание)")
            self.results['passed'] += 1
        else:
            print(f"  ✗ /clients/create/ POST (Ошибка: {response.status_code})")
            self.results['failed'] += 1
        
        # Редактирование клиента
        self.test_route(f'/clients/{test_client.pk}/edit/', expected_status=200)
        
        # Редактирование через POST
        response = self.client.post(f'/clients/{test_client.pk}/edit/', {
            'first_name': 'Обновлённый',
            'last_name': 'Клиент',
            'phone': '+79991112233',
            'email': 'testclient@example.com',
            'status': 'ACTIVE'
        })
        if response.status_code == 302:
            print(f"  ✓ /clients/{test_client.pk}/edit/ POST (302 - обновление)")
            self.results['passed'] += 1
        else:
            print(f"  ✗ /clients/{test_client.pk}/edit/ POST (Ошибка: {response.status_code})")
            self.results['failed'] += 1
    
    def test_course_routes(self):
        """Тестирование работы с курсами"""
        print("\n" + "="*60)
        print("4. КУРСЫ")
        print("="*60)
        
        self.client.login(username='test_admin', password='testpass123')
        
        # Список курсов
        self.test_route('/courses/', expected_status=200)
        
        # Создаём категорию и курс
        category, _ = CourseCategory.objects.get_or_create(
            name='DJ-инг',
            slug='dj-ing'
        )
        
        test_course, _ = Course.objects.get_or_create(
            slug='test-basic-course',
            defaults={
                'name': 'Тестовый Базовый Курс',
                'category': category,
                'total_lessons': 10,
                'lesson_duration': 60,
                'base_price': Decimal('30000.00'),
                'description': 'Тестовый курс'
            }
        )
        
        # Детали курса
        self.test_route(f'/courses/{test_course.pk}/', expected_status=200)
        
        # Форма создания курса
        self.test_route('/courses/create/', expected_status=200)
        
        # Создание курса через POST
        response = self.client.post('/courses/create/', {
            'name': 'Новый Курс',
            'slug': 'new-course',
            'category': category.pk,
            'description': 'Описание',
            'total_lessons': 12,
            'lesson_duration': 60,
            'base_price': '25000',
            'is_active': 'on'
        })
        if response.status_code == 302:
            print(f"  ✓ /courses/create/ POST (302 - создание)")
            self.results['passed'] += 1
        else:
            print(f"  ✗ /courses/create/ POST (Ошибка: {response.status_code})")
            self.results['failed'] += 1
        
        # Редактирование курса
        self.test_route(f'/courses/{test_course.pk}/edit/', expected_status=200)
        
        # Форма записи на курс
        self.test_route(f'/courses/{test_course.pk}/enroll/', expected_status=200)
        
        # Запись клиента на курс через POST
        test_client, _ = Client.objects.get_or_create(
            phone='+79991112233',
            defaults={
                'first_name': 'Тестовый',
                'last_name': 'Клиент',
                'status': 'ACTIVE'
            }
        )
        
        response = self.client.post(f'/courses/{test_course.pk}/enroll/', {
            'client_id': test_client.pk,
            'start_date': date.today().strftime('%Y-%m-%d'),
            'enrolled_price': '30000',
            'installment_type': 'NONE',
            'source': 'Тест'
        })
        if response.status_code == 302:
            print(f"  ✓ /courses/{test_course.pk}/enroll/ POST (302 - запись)")
            self.results['passed'] += 1
        else:
            print(f"  ✗ /courses/{test_course.pk}/enroll/ POST (Ошибка: {response.status_code})")
            self.results['failed'] += 1
            if hasattr(response, 'content'):
                print(f"    Детали: {response.content[:200]}")
    
    def test_enrollment_routes(self):
        """Тестирование записей на курсы"""
        print("\n" + "="*60)
        print("5. ЗАПИСИ НА КУРСЫ")
        print("="*60)
        
        self.client.login(username='test_admin', password='testpass123')
        
        # Список записей
        self.test_route('/enrollments/', expected_status=200)
        
        # Создаём тестовую запись
        test_client, _ = Client.objects.get_or_create(
            phone='+79991112233',
            defaults={'first_name': 'Тест', 'last_name': 'Клиент', 'status': 'ACTIVE'}
        )
        
        category, _ = CourseCategory.objects.get_or_create(name='DJ-инг', slug='dj-ing')
        test_course, _ = Course.objects.get_or_create(
            slug='test-enrollment-course',
            defaults={
                'name': 'Тест Курс',
                'category': category,
                'total_lessons': 10,
                'lesson_duration': 60,
                'base_price': Decimal('30000.00')
            }
        )
        
        enrollment, _ = Enrollment.objects.get_or_create(
            course=test_course,
            client=test_client,
            start_date=date.today(),
            defaults={
                'total_lessons': 10,
                'total_practice_hours': 30,
                'enrolled_price': Decimal('30000.00'),
                'status': 'ACTIVE'
            }
        )
        
        # Детали записи
        self.test_route(f'/enrollments/{enrollment.pk}/', expected_status=200)
    
    def test_payment_routes(self):
        """Тестирование платежей"""
        print("\n" + "="*60)
        print("6. ПЛАТЕЖИ")
        print("="*60)
        
        self.client.login(username='test_admin', password='testpass123')
        
        # Список платежей
        self.test_route('/payments/', expected_status=200)
        
        # Создаём тестовый платёж
        test_client, _ = Client.objects.get_or_create(
            phone='+79991112233',
            defaults={'first_name': 'Тест', 'last_name': 'Клиент'}
        )
        
        Payment.objects.get_or_create(
            client=test_client,
            amount=Decimal('10000.00'),
            defaults={
                'status': 'COMPLETED',
                'payment_type': 'ONCE'
            }
        )
    
    def test_task_routes(self):
        """Тестирование задач"""
        print("\n" + "="*60)
        print("7. ЗАДАЧИ")
        print("="*60)
        
        self.client.login(username='test_admin', password='testpass123')
        
        # Список задач
        self.test_route('/tasks/', expected_status=200)
        
        # Создаём тестовую задачу
        test_client, _ = Client.objects.get_or_create(
            phone='+79991112233',
            defaults={'first_name': 'Тест', 'last_name': 'Клиент'}
        )
        
        Task.objects.get_or_create(
            title='Тестовая задача',
            client=test_client,
            defaults={
                'assigned_to': self.test_user,
                'due_date': date.today() + timedelta(days=7),
                'priority': 'MEDIUM',
                'status': 'TODO'
            }
        )
    
    def test_schedule_routes(self):
        """Тестирование расписания"""
        print("\n" + "="*60)
        print("8. РАСПИСАНИЕ")
        print("="*60)
        
        self.client.login(username='test_admin', password='testpass123')
        
        # Расписание
        self.test_route('/schedule/', expected_status=200)
        
        # Создаём тестовое занятие
        test_client, _ = Client.objects.get_or_create(
            phone='+79991112233',
            defaults={'first_name': 'Тест', 'last_name': 'Клиент'}
        )
        
        lesson_type, _ = LessonType.objects.get_or_create(
            name='Миксинг',
            slug='mixing',
            defaults={'color': '#3788d8'}
        )
        
        test_teacher_profile, _ = EmployeeProfile.objects.get_or_create(
            user=self.test_teacher,
            defaults={'hire_date': date.today()}
        )
        
        Lesson.objects.get_or_create(
            client=test_client,
            lesson_type=lesson_type,
            start_time=timezone.now() + timedelta(days=1),
            defaults={
                'status': 'planned',
                'lesson_type_detail': 'STANDARD',
                'duration_minutes': 60,
                'teacher': test_teacher_profile
            }
        )
    
    def test_manager_routes(self):
        """Тестирование панели менеджера"""
        print("\n" + "="*60)
        print("9. ПАНЕЛЬ МЕНЕДЖЕРА")
        print("="*60)
        
        self.client.login(username='test_admin', password='testpass123')
        
        # Дашборд менеджера
        self.test_route('/manager/', expected_status=200)
        
        # Клиенты менеджера
        self.test_route('/manager/clients/', expected_status=200)
        
        # Записи менеджера
        self.test_route('/manager/enrollments/', expected_status=200)
        
        # Платежи менеджера
        self.test_route('/manager/payments/', expected_status=200)
    
    def test_teacher_routes(self):
        """Тестирование дашборда преподавателя"""
        print("\n" + "="*60)
        print("10. ДАШБОРД ПРЕПОДАВАТЕЛЯ")
        print("="*60)
        
        self.client.login(username='test_teacher', password='testpass123')
        
        # Дашборд преподавателя
        self.test_route('/teacher/', expected_status=200)
        
        # Расписание преподавателя
        self.test_route('/teacher/schedule/', expected_status=200)
        
        # Студенты преподавателя
        self.test_route('/teacher/students/', expected_status=200)
    
    def test_student_routes(self):
        """Тестирование личного кабинета студента"""
        print("\n" + "="*60)
        print("11. ЛИЧНЫЙ КАБИНЕТ СТУДЕНТА")
        print("="*60)
        
        self.client.login(username='test_student', password='testpass123')
        
        # Дашборд студента
        self.test_route('/student/', expected_status=200)
        
        # Занятия студента
        self.test_route('/student/lessons/', expected_status=200)
        
        # Платежи студента
        self.test_route('/student/payments/', expected_status=200)
    
    def test_model_operations(self):
        """Тестирование операций с моделями"""
        print("\n" + "="*60)
        print("12. ОПЕРАЦИИ С МОДЕЛЯМИ")
        print("="*60)
        
        try:
            # Тест Enrollment properties
            test_client, _ = Client.objects.get_or_create(
                phone='+79999999999',
                defaults={'first_name': 'Тест', 'last_name': 'Model', 'status': 'ACTIVE'}
            )
            
            category, _ = CourseCategory.objects.get_or_create(name='Тест', slug='test-cat')
            test_course, _ = Course.objects.get_or_create(
                slug='test-model-course',
                defaults={
                    'name': 'Тест Курс',
                    'category': category,
                    'total_lessons': 10,
                    'lesson_duration': 60,
                    'base_price': Decimal('30000.00')
                }
            )
            
            enrollment, _ = Enrollment.objects.get_or_create(
                course=test_course,
                client=test_client,
                start_date=date.today(),
                defaults={
                    'total_lessons': 10,
                    'total_practice_hours': 30,
                    'enrolled_price': Decimal('30000.00'),
                    'status': 'ACTIVE'
                }
            )
            
            # Тест свойств
            remaining = enrollment.remaining_lessons
            progress = enrollment.progress_percentage
            is_completed = enrollment.is_completed
            
            print(f"  ✓ Enrollment.remaining_lessons: {remaining}")
            print(f"  ✓ Enrollment.progress_percentage: {progress}%")
            print(f"  ✓ Enrollment.is_completed: {is_completed}")
            
            # Тест update_progress
            enrollment.update_progress()
            print(f"  ✓ Enrollment.update_progress() выполнен")
            
            self.results['passed'] += 4
            
            # Тест Notification создание
            notification = Notification.objects.create(
                client=test_client,
                notification_type='LESSON_REMINDER_24H',
                title='Тест уведомления',
                message='Текст уведомления',
                send_method='EMAIL',
                status='PENDING'
            )
            print(f"  ✓ Notification создан: {notification}")
            self.results['passed'] += 1
            
        except Exception as e:
            print(f"  ✗ Ошибка тестирования моделей: {str(e)[:100]}")
            self.results['failed'] += 1
            self.results['errors'].append(f"Model operations: {str(e)}")
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("\n" + "="*60)
        print("КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ DJ CRM")
        print("="*60)
        print(f"Начало тестирования: {timezone.now()}")
        
        try:
            self.test_authentication()
            self.test_dashboard_routes()
            self.test_client_routes()
            self.test_course_routes()
            self.test_enrollment_routes()
            self.test_payment_routes()
            self.test_task_routes()
            self.test_schedule_routes()
            self.test_manager_routes()
            self.test_teacher_routes()
            self.test_student_routes()
            self.test_model_operations()
            
        except Exception as e:
            print(f"\nКритическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        
        # Итоговый отчёт
        print("\n" + "="*60)
        print("ИТОГИ ТЕСТИРОВАНИЯ")
        print("="*60)
        print(f"Пройдено: {self.results['passed']}")
        print(f"Не пройдено: {self.results['failed']}")
        print(f"Всего тестов: {self.results['passed'] + self.results['failed']}")
        
        if self.results['errors']:
            print(f"\nОшибки:")
            for error in self.results['errors'][:10]:
                print(f"  - {error}")
        
        success_rate = (self.results['passed'] / (self.results['passed'] + self.results['failed'])) * 100 if (self.results['passed'] + self.results['failed']) > 0 else 0
        print(f"\nУспешность: {success_rate:.1f}%")
        
        return self.results['failed'] == 0


if __name__ == '__main__':
    tester = CRMTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)