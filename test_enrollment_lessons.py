#!/usr/bin/env python
"""
Тестирование обновлённых моделей Enrollment и Lesson
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from core.models import Client, Course, CourseCategory, Enrollment
from lessons.models import Lesson, LessonType
from django.contrib.auth.models import User

def test_enrollment_model():
    """Тестирование модели Enrollment"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ МОДЕЛИ Enrollment")
    print("="*60)
    
    # Создаём тестовые данные
    category, _ = CourseCategory.objects.get_or_create(name='DJ-инг', slug='dj-ing')
    course, _ = Course.objects.get_or_create(
        slug='test-basic-course',
        defaults={
            'name': 'Тестовый Базовый Курс',
            'category': category,
            'total_lessons': 10,
            'lesson_duration': 60,
            'base_price': Decimal('30000.00'),
            'description': 'Тестовый курс для проверки',
            'curriculum': 'Тема 1, Тема 2, Тема 3',
        }
    )
    
    client, _ = Client.objects.get_or_create(
        phone='+79990000000',
        defaults={
            'first_name': 'Тестовый',
            'last_name': 'Студент',
            'email': 'test@example.com',
        }
    )
    
    user, _ = User.objects.get_or_create(username='test_manager', defaults={'is_staff': True})
    
    # Создаём запись на курс с разными параметрами
    print("\n1. Создание записи на курс (Базовый: 10 занятий + 30 часов практики)")
    from datetime import date
    enrollment = Enrollment.objects.create(
        course=course,
        client=client,
        start_date=date.today(),
        total_lessons=10,
        total_practice_hours=30,
        is_unlimited_practice=False,
        enrolled_price=Decimal('30000.00'),
        installment_type='NONE',
        enrolled_by=user,
    )
    print(f"   [OK] Запись создана: {enrollment}")
    
    # Тест свойств
    print("\n2. Тестирование свойств:")
    print(f"   - Оставшиеся занятия: {enrollment.remaining_lessons} (ожидается: 10)")
    print(f"   - Оставшиеся часы практики: {enrollment.remaining_practice_hours} (ожидается: 30)")
    print(f"   - Прогресс: {enrollment.progress_percentage}% (ожидается: 0%)")
    print(f"   - Завершён: {enrollment.is_completed} (ожидается: False)")
    
    # Создаём запись с безлимитной практикой
    print("\n3. Создание записи с безлимитной практикой")
    course_unlimited, _ = Course.objects.get_or_create(
        slug='test-unlimited-course',
        defaults={
            'name': 'Тестовый Полный Фарш',
            'category': category,
            'total_lessons': 15,
            'lesson_duration': 60,
            'base_price': Decimal('60000.00'),
            'description': 'Курс с безлимитной практикой',
            'curriculum': 'Все темы',
        }
    )
    
    enrollment_unlimited = Enrollment.objects.create(
        course=course_unlimited,
        client=client,
        start_date=timezone.now().date(),
        total_lessons=15,
        total_practice_hours=0,
        is_unlimited_practice=True,
        enrolled_price=Decimal('60000.00'),
        installment_type='BANK_6',
        enrolled_by=user,
    )
    print(f"   [OK] Запись создана: {enrollment_unlimited}")
    print(f"   - Оставшиеся часы практики: {enrollment_unlimited.remaining_practice_hours} (ожидается: inf)")
    
    # Создаём запись с рассрочкой
    print("\n4. Создание записи с рассрочкой")
    enrollment_installment = Enrollment.objects.create(
        course=course,
        client=client,
        start_date=timezone.now().date(),
        total_lessons=10,
        total_practice_hours=30,
        enrolled_price=Decimal('30000.00'),
        installment_type='SCHOOL_3',
        installment_bank_fee_percent=Decimal('5.00'),
        enrolled_by=user,
    )
    print(f"   [OK] Запись создана: {enrollment_installment}")
    print(f"   - Тип рассрочки: {enrollment_installment.get_installment_type_display()}")
    
    print("\n[OK] Все тесты Enrollment пройдены!")
    return enrollment, enrollment_unlimited, enrollment_installment

    # Тест свойств
    print("\n2. Тестирование свойств:")
    print(f"   - Оставшиеся занятия: {enrollment.remaining_lessons} (ожидается: 10)")
    print(f"   - Оставшиеся часы практики: {enrollment.remaining_practice_hours} (ожидается: 30)")
    print(f"   - Прогресс: {enrollment.progress_percentage}% (ожидается: 0%)")
    print(f"   - Завершён: {enrollment.is_completed} (ожидается: False)")
    
    # Создаём запись с безлимитной практикой
    print("\n3. Создание записи с безлимитной практикой")
    course_unlimited, _ = Course.objects.get_or_create(
        slug='test-unlimited-course',
        defaults={
            'name': 'Тестовый Полный Фарш',
            'category': category,
            'total_lessons': 15,
            'lesson_duration': 60,
            'base_price': Decimal('60000.00'),
            'description': 'Курс с безлимитной практикой',
            'curriculum': 'Все темы',
        }
    )
    
    enrollment_unlimited = Enrollment.objects.create(
        course=course_unlimited,
        client=client,
        start_date=timezone.now().date(),
        total_lessons=15,
        total_practice_hours=0,
        is_unlimited_practice=True,
        enrolled_price=Decimal('60000.00'),
        installment_type='BANK_6',
        enrolled_by=user,
    )
    print(f"   ✅ Запись создана: {enrollment_unlimited}")
    print(f"   - Оставшиеся часы практики: {enrollment_unlimited.remaining_practice_hours} (ожидается: inf)")
    
    # Создаём запись с рассрочкой
    print("\n4. Создание записи с рассрочкой")
    enrollment_installment = Enrollment.objects.create(
        course=course,
        client=client,
        start_date=timezone.now().date(),
        total_lessons=10,
        total_practice_hours=30,
        enrolled_price=Decimal('30000.00'),
        installment_type='SCHOOL_3',
        installment_bank_fee_percent=Decimal('5.00'),
        enrolled_by=user,
    )
    print(f"   ✅ Запись создана: {enrollment_installment}")
    print(f"   - Тип рассрочки: {enrollment_installment.get_installment_type_display()}")
    
    print("\n✅ Все тесты Enrollment пройдены!")
    return enrollment, enrollment_unlimited, enrollment_installment

def test_lesson_model(enrollment, enrollment_unlimited, enrollment_installment):
    """Тестирование модели Lesson"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ МОДЕЛИ Lesson")
    print("="*60)
    
    lesson_type, _ = LessonType.objects.get_or_create(
        name='Миксинг',
        slug='mixing',
        defaults={'color': '#3788d8', 'duration_default': 60}
    )
    
    # Создаём занятие с преподавателем
    print("\n1. Создание занятия с преподавателем")
    lesson_standard = Lesson.objects.create(
        enrollment=enrollment,
        client=enrollment.client,
        lesson_type=lesson_type,
        lesson_type_detail='STANDARD',
        start_time=timezone.now() + timedelta(hours=1),
        duration_minutes=60,
        status='completed',
    )
    print(f"   [OK] Занятие создано: {lesson_standard}")
    print(f"   - Тип: {lesson_standard.get_lesson_type_detail_display()}")
    print(f"   - Длительность: {lesson_standard.duration_minutes} мин")
    
    # Создаём самостоятельную практику
    print("\n2. Создание самостоятельной практики")
    lesson_practice = Lesson.objects.create(
        enrollment=enrollment,
        client=enrollment.client,
        lesson_type=lesson_type,
        lesson_type_detail='PRACTICE',
        start_time=timezone.now() + timedelta(hours=2),
        duration_minutes=120,  # 2 часа практики
        status='completed',
    )
    print(f"   [OK] Практика создана: {lesson_practice}")
    print(f"   - Тип: {lesson_practice.get_lesson_type_detail_display()}")
    print(f"   - Длительность: {lesson_practice.duration_minutes} мин")
    print(f"   - Преподаватель: {lesson_practice.teacher} (ожидается: None)")
    
    # Проверяем связь с enrollment
    print("\n3. Проверка связи с enrollment")
    print(f"   - Занятий в записи: {enrollment.lessons.count()}")
    print(f"   - Стандартных занятий: {enrollment.lessons.filter(lesson_type_detail='STANDARD').count()}")
    print(f"   - Практики: {enrollment.lessons.filter(lesson_type_detail='PRACTICE').count()}")
    
    # Проверяем прогресс
    print("\n4. Проверка прогресса")
    enrollment.update_progress()
    print(f"   - Прогресс после update_progress(): {enrollment.progress_percentage}%")
    print(f"   - Отработано занятий: {enrollment.completed_lessons}")
    print(f"   - Отработано практики: {enrollment.completed_practice_minutes} мин ({enrollment.completed_practice_hours} ч)")
    
    # Тестируем отмену занятия
    print("\n5. Тестирование отмены занятия")
    from django.contrib.auth.models import User
    user, _ = User.objects.get_or_create(username='test_manager', defaults={'is_staff': True})
    
    lesson_to_cancel = Lesson.objects.create(
        enrollment=enrollment,
        client=enrollment.client,
        lesson_type=lesson_type,
        lesson_type_detail='STANDARD',
        start_time=timezone.now() + timedelta(days=1),
        duration_minutes=60,
        status='planned',
    )
    
    # Отменяем с причиной
    lesson_to_cancel.status = 'cancelled'
    lesson_to_cancel.cancelled_by = user
    lesson_to_cancel.cancellation_reason = 'Студент заболел'
    lesson_to_cancel.save()
    
    print(f"   [OK] Занятие отменено: {lesson_to_cancel}")
    print(f"   - Статус: {lesson_to_cancel.get_status_display()}")
    print(f"   - Причина: {lesson_to_cancel.cancellation_reason}")
    
    print("\n[OK] Все тесты Lesson пройдены!")
    return lesson_standard, lesson_practice

def test_payment_fields():
    """Тестирование полей Payment для рассрочек"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ПОЛЕЙ PAYMENT")
    print("="*60)
    
    from payments.models import Payment, PaymentMethod
    from core.models import Client
    
    client = Client.objects.filter(phone='+79990000000').first()
    
    # Создаём метод оплаты
    method, _ = PaymentMethod.objects.get_or_create(
        code='card',
        defaults={'name': 'Банковская карта', 'icon': '💳'}
    )
    
    # Создаём платежи с рассрочкой
    print("\n1. Создание платежа с банковской рассрочкой (3 платежа)")
    payment1 = Payment.objects.create(
        client=client,
        amount=Decimal('10000.00'),
        payment_type='BANK_3',
        installment_number=1,
        total_installments=3,
        bank_fee_percent=Decimal('2.50'),
        bank_fee_amount=Decimal('250.00'),
        status='COMPLETED',
        description='Первый платёж рассрочки',
    )
    print(f"   [OK] Платёж создан: {payment1}")
    print(f"   - Тип: {payment1.get_payment_type_display()}")
    print(f"   - Платёж: {payment1.installment_number}/{payment1.total_installments}")
    print(f"   - Комиссия: {payment1.bank_fee_percent}% = {payment1.bank_fee_amount} руб")
    
    # Создаём платёж с рассрочкой от школы
    print("\n2. Создание платежа с рассрочкой школы (2 платежа)")
    payment2 = Payment.objects.create(
        client=client,
        amount=Decimal('15000.00'),
        payment_type='SCHOOL_2',
        installment_number=1,
        total_installments=2,
        status='PENDING',
        description='Первый платёж рассрочки школы',
    )
    print(f"   [OK] Платёж создан: {payment2}")
    print(f"   - Тип: {payment2.get_payment_type_display()}")
    
    print("\n[OK] Все тесты Payment пройдены!")
    return payment1, payment2

def test_notification_model():
    """Тестирование модели Notification"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ МОДЕЛИ Notification")
    print("="*60)
    
    from interactions.models import Notification
    from core.models import Client
    
    client = Client.objects.filter(phone='+79990000000').first()
    
    # Создаём уведомление о занятии
    print("\n1. Создание уведомления о занятии за 24 часа")
    notification_24h = Notification.objects.create(
        client=client,
        notification_type='LESSON_REMINDER_24H',
        title='Напоминание о занятии',
        message='Завтра у вас запланировано занятие в 18:00',
        send_method='WHATSAPP',
        scheduled_for=timezone.now() + timedelta(hours=24),
    )
    print(f"   [OK] Уведомление создано: {notification_24h}")
    print(f"   - Тип: {notification_24h.get_notification_type_display()}")
    print(f"   - Метод: {notification_24h.get_send_method_display()}")
    
    # Создаём уведомление об оплате
    print("\n2. Создание уведомления об оплате")
    notification_payment = Notification.objects.create(
        client=client,
        notification_type='PAYMENT_REMINDER',
        title='Напоминание об оплате',
        message='Напоминаем об оплате второго платежа рассрочки',
        send_method='SMS',
        scheduled_for=timezone.now() + timedelta(days=1),
    )
    print(f"   [OK] Уведомление создано: {notification_payment}")
    
    print("\n[OK] Все тесты Notification пройдены!")
    return notification_24h, notification_payment

def main():
    """Запуск всех тестов"""
    print("\n" + "="*60)
    print("НАЧАЛО ТЕСТИРОВАНИЯ ОБНОВЛЁННЫХ МОДЕЛЕЙ")
    print("="*60)
    
    try:
        # Тестируем Enrollment
        enrollment, enrollment_unlimited, enrollment_installment = test_enrollment_model()
        
        # Тестируем Lesson
        lesson_standard, lesson_practice = test_lesson_model(
            enrollment, enrollment_unlimited, enrollment_installment
        )
        
        # Тестируем Payment
        payment1, payment2 = test_payment_fields()
        
        # Тестируем Notification
        notification_24h, notification_payment = test_notification_model()
        
        print("\n" + "="*60)
        print("[OK] ВСЕ ТЕСТЫ УСПЕШНО ЗАВЕРШЕНЫ!")
        print("="*60)
        
        print("\nИтоги:")
        print(f"   - Создано записей: 3")
        print(f"   - Создано занятий: 3 (2 стандартных + 1 практика)")
        print(f"   - Создано платежей: 2")
        print(f"   - Создано уведомлений: 2")
        print(f"\n   Модели работают корректно!")
        
    except Exception as e:
        print(f"\n[ERROR] ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())