from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.signing import Signer
from django.contrib import messages
from clients.models import Client
from products.models import Enrollment, Payment
from lessons.models import Lesson
from .models import ClientCabinetProfile
from .forms import ProfileForm, PasswordChangeForm, RegisterForm
from django.utils import timezone


def register(request):
    """Страница регистрации"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            phone = form.cleaned_data.get('phone')
            
            # Очистим телефон от лишних символов для поиска
            phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            # 1. Ищем клиента в CRM по телефону
            try:
                client = Client.objects.get(phone=phone_clean)
            except Client.DoesNotExist:
                messages.error(request, 'Клиент с таким телефоном не найден в базе')
                return render(request, 'client_cabinet/register.html', {'form': form})
            
            # 2. Проверяем наличие активного Enrollment
            enrollment = Enrollment.objects.filter(client=client, status='active').first()
            if not enrollment:
                messages.error(request, 'У вас нет активных занятий. Обратитесь к администратору')
                return render(request, 'client_cabinet/register.html', {'form': form})
            
            # 3. Проверяем, не зарегистрирован ли уже этот клиент
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Этот email уже зарегистрирован')
                return render(request, 'client_cabinet/register.html', {'form': form})
            
            # 4. Создаём пользователя
            user = User.objects.create_user(username=username, email=email, password=password)
            
            # 5. Создаём профиль кабинета и связываем с Client
            profile = ClientCabinetProfile.objects.create(user=user, phone=phone_clean)
            profile.client = client  # Связь с CRM
            profile.save()
            
            # 6. Генерируем токен подтверждения
            signer = Signer()
            token = signer.sign(f'{user.id}:{user.email}')
            
            # 7. Отправляем письмо
            send_mail(
                'Подтверждение email — MUSERP',
                f'Перейдите по ссылке: http://muserp.na4u.ru/cabinet/confirm-email/{token}/',
                'noreply@muserp.na4u.ru',
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'Регистрация успешна! Проверьте почту')
            return redirect('client_cabinet:confirm_email')
    else:
        form = RegisterForm()
    
    return render(request, 'client_cabinet/register.html', {'form': form})


@login_required
def confirm_email(request):
    """Страница подтверждения email"""
    return render(request, 'client_cabinet/confirm_email.html')


@login_required
def dashboard(request):
    """Главная страница личного кабинета"""
    profile = request.user.clientcabinetprofile
    client = profile.client
    
    # Следующее занятие
    next_lesson = Lesson.objects.filter(
        client=client,
        status='scheduled',
        start_time__gte=timezone.now()
    ).select_related('teacher', 'room').order_by('start_time').first()
    
    # Количество активных курсов
    active_courses_count = Enrollment.objects.filter(
        client=client,
        status='active'
    ).count()
    
    context = {
        'client': client,
        'next_lesson': next_lesson,
        'active_courses_count': active_courses_count,
    }
    
    return render(request, 'client_cabinet/dashboard.html', context)


@login_required
def schedule(request):
    """Расписание занятий клиента"""
    profile = request.user.clientcabinetprofile
    client = profile.client
    
    now = timezone.now()
    
    # Разделяем на будущие и прошедшие
    upcoming_lessons = Lesson.objects.filter(
        client=client, 
        start_time__gte=now
    ).select_related('teacher', 'room').order_by('start_time')
    
    past_lessons = Lesson.objects.filter(
        client=client, 
        start_time__lt=now
    ).select_related('teacher', 'room').order_by('-start_time')[:20]

    context = {
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
    }

    return render(request, 'client_cabinet/schedule.html', context)


#@login_required
#def purchases(request):
#    """История покупок"""
#    profile = request.user.clientcabinetprofile
#    client = profile.client
#    
#    enrollments_qs = Enrollment.objects.filter(
#        client=client
#    ).select_related('product').order_by('-created_at')
#    
#    # Добавляем процент прогресса к каждому абонементу
#    enrollments = []
#    for enrollment in enrollments_qs:
#        progress_percent = 0
#        if enrollment.lessons_total and enrollment.lessons_total > 0:
#            progress_percent = round(enrollment.lessons_used * 100 / enrollment.lessons_total)
#        enrollments.append({
#            'enrollment': enrollment,
#            'progress_percent': progress_percent,
#        })
#    
#    context = {
#        'enrollments': enrollments,
#    }
#    
#    return render(request, 'client_cabinet/purchases.html', context)


#@login_required
#def payments(request):
#    """Баланс и оплаты — история платежей и задолженность"""
#    profile = request.user.clientcabinetprofile
#    client = profile.client
#    
#    payments_list = Payment.objects.filter(
#        enrollment__client=client
#    ).select_related('enrollment__product').order_by('installment_number')
#    
#    total_paid = sum(float(p.amount_paid_by_client) for p in payments_list if p.is_paid)
#    total_due = sum(float(p.amount_paid_by_client) for p in payments_list if not p.is_paid)
#    total_amount = total_paid + total_due
#    
#    next_payment = payments_list.filter(is_paid=False).order_by('due_date').first()
#    
#    context = {
#        'payments': payments_list,
#        'total_paid': total_paid,
#        'total_due': total_due,
#        'total_amount': total_amount,
#        'next_payment': next_payment,
#    }
#    
#    return render(request, 'client_cabinet/payments.html', context)


@login_required
def profile_edit(request):
    """Редактирование профиля — телефон"""
    profile = request.user.clientcabinetprofile
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён.')
            return redirect('client_cabinet:profile_edit')
    else:
        form = ProfileForm(instance=profile)
    
    context = {
        'form': form,
        'email': request.user.email,
    }
    
    return render(request, 'client_cabinet/profile_edit.html', context)


@login_required
def password_change(request):
    """Смена пароля"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password1']
            
            if not request.user.check_password(old_password):
                form.add_error('old_password', 'Неверный текущий пароль.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Пароль успешно изменён.')
                return redirect('client_cabinet:dashboard')
    else:
        form = PasswordChangeForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'client_cabinet/password_change.html', context)


#@login_required
#def progress(request):
#    """Прогресс обучения — статистика посещаемости"""
#    profile = request.user.clientcabinetprofile
#    client = profile.client
#    
#    # Получаем активные абонементы
#    enrollments_qs = Enrollment.objects.filter(client=client, status='active').select_related('product')
#    
#    # Добавляем процент прогресса к каждому абонементу
#    enrollments = []
#    for enrollment in enrollments_qs:
#        progress_percent = 0
#        if enrollment.lessons_total > 0:
#            progress_percent = round(enrollment.lessons_used * 100 / enrollment.lessons_total)
#        enrollments.append({
#            'enrollment': enrollment,
#            'progress_percent': progress_percent,
#        })
#    
#    # Получаем все занятия клиента
#    lessons = Lesson.objects.filter(client=client)
#    completed = lessons.filter(status='completed').count()
#    scheduled = lessons.filter(status='scheduled').count()
#    cancelled = lessons.filter(status='cancelled').count()
#    
#    # Получаем последние занятия
#    recent_lessons = lessons.select_related('teacher', 'room').order_by('-start_time')[:10]
#    
#    context = {
#        'enrollments': enrollments,
#        'lessons_completed': completed,
#        'lessons_scheduled': scheduled,
#        'lessons_cancelled': cancelled,
#        'lessons_total': lessons.count(),
#        'recent_lessons': recent_lessons,
#    }
#    
#    return render(request, 'client_cabinet/progress.html', context)
    
    
@login_required
def courses(request):
    """Мои курсы — абонементы с прогрессом"""
    profile = request.user.clientcabinetprofile
    client = profile.client
    
    # Получаем все абонементы клиента
    enrollments_qs = Enrollment.objects.filter(
        client=client
    ).select_related('product').order_by('-created_at')
    
    # Добавляем данные к каждому абонементу
    enrollments = []
    for enrollment in enrollments_qs:
        progress_percent = 0
        if enrollment.lessons_total and enrollment.lessons_total > 0:
            progress_percent = round(enrollment.lessons_used * 100 / enrollment.lessons_total)
        
        # Получаем занятия по этому абонементу
        lessons = Lesson.objects.filter(client=client)
        completed = lessons.filter(status='completed').count()
        scheduled = lessons.filter(status='scheduled').count()
        
        # Следующее занятие
        next_lesson = lessons.filter(
            status='scheduled',
            start_time__gte=timezone.now()
        ).select_related('teacher', 'room').order_by('start_time').first()
        
        enrollments.append({
            'enrollment': enrollment,
            'progress_percent': progress_percent,
            'lessons_completed': completed,
            'lessons_scheduled': scheduled,
            'next_lesson': next_lesson,
        })
    
    context = {
        'enrollments': enrollments,
    }
    
    return render(request, 'client_cabinet/courses.html', context)


@login_required
def installments(request):
    """Рассрочка — только если есть активная рассрочка"""
    profile = request.user.clientcabinetprofile
    client = profile.client
    
    payments_list = Payment.objects.filter(
        enrollment__client=client
    ).select_related('enrollment__product').order_by('installment_number')
    
    # Показываем только если есть неоплаченные платежи
    has_installment = payments_list.filter(is_paid=False).exists()
    
    total_paid = sum(float(p.amount_paid_by_client) for p in payments_list if p.is_paid)
    total_due = sum(float(p.amount_paid_by_client) for p in payments_list if not p.is_paid)
    
    next_payment = payments_list.filter(is_paid=False).order_by('due_date').first()
    
    context = {
        'payments': payments_list,
        'has_installment': has_installment,
        'total_paid': total_paid,
        'total_due': total_due,
        'next_payment': next_payment,
    }
    
    return render(request, 'client_cabinet/installments.html', context)
    

def confirm_email_token(request, token):
    """Подтверждение email по ссылке из письма"""
    signer = Signer()
    try:
        data = signer.unsign(token, max_age=86400)
        user_id, email = data.split(':')
        user = User.objects.get(id=user_id)
        profile = ClientCabinetProfile.objects.get(user=user)
        profile.email_confirmed = True
        profile.save()
        login(request, user)
        return redirect('client_cabinet:dashboard')
    except Exception:
        return redirect('client_cabinet:confirm_email')