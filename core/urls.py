from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Дашборд и авторизация
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Клиенты
    path('clients/', views.client_list, name='client_list'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/create-interaction/', views.create_interaction, name='create_interaction'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:client_id>/edit/', views.client_update, name='client_update'),
    path('clients/<int:client_id>/delete/', views.client_delete, name='client_delete'),
    
    # Курсы
    path('courses/', views.courses_list, name='courses_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:course_id>/edit/', views.course_update, name='course_update'),
    path('courses/<int:course_id>/enroll/', views.enroll_client, name='enroll_client'),
    
    # Записи на курсы
    path('enrollments/', views.enrollments_list, name='enrollments_list'),
    path('enrollments/<int:enrollment_id>/', views.enrollment_detail, name='enrollment_detail'),
    
    # Платежи
    path('payments/', views.payments_list, name='payments_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:payment_id>/edit/', views.payment_update, name='payment_update'),
    path('payments/<int:payment_id>/delete/', views.payment_delete, name='payment_delete'),
    path('payments/<int:payment_id>/pay/', views.payment_pay, name='payment_pay'),
    
    # Задачи
    path('tasks/', views.tasks_list, name='tasks_list'),
    
    # Расписание
    path('schedule/', views.schedule_view, name='schedule'),
    
    # === ЛИЧНЫЙ КАБИНЕТ СТУДЕНТА ===
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/lessons/', views.student_lessons, name='student_lessons'),
    path('student/payments/', views.student_payments, name='student_payments'),
    path('student/progress/<int:enrollment_id>/', views.student_progress, name='student_progress'),
    
    # === ДАШБОРД ПРЕПОДАВАТЕЛЯ ===
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/schedule/', views.teacher_schedule, name='teacher_schedule'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/lesson/<int:lesson_id>/mark/', views.teacher_lesson_mark, name='teacher_lesson_mark'),
    
    # === ПАНЕЛЬ МЕНЕДЖЕРА ===
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/clients/', views.manager_clients_quick, name='manager_clients_quick'),
    path('manager/enrollments/', views.manager_enrollments_quick, name='manager_enrollments_quick'),
    path('manager/payments/', views.manager_payments_quick, name='manager_payments_quick'),
    
    # === НАСТРОЙКИ ===
    path('settings/', views.settings_view, name='settings'),
    path('settings/tariffs/', views.tariffs_list, name='tariffs_list'),
    path('settings/tariffs/create/', views.tariff_create, name='tariff_create'),
    path('settings/tariffs/<int:tariff_id>/edit/', views.tariff_update, name='tariff_update'),
    path('settings/tariffs/<int:tariff_id>/delete/', views.tariff_delete, name='tariff_delete'),
]
