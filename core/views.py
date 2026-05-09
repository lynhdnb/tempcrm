from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta, date, datetime
from decimal import Decimal

from .models import Client, RoleAssignment, EmployeeProfile, Course, CourseCategory, Enrollment, ClientComment, Tariff
from interactions.models import Interaction, Notification
from lessons.models import Lesson
from payments.models import Payment, Invoice, PaymentMethod
from tasks.models import Task


def login_view(request):
    """Страница входа"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    error = None
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('core:dashboard')
        else:
            error = 'Неверный логин или пароль'
    
    return render(request, 'login.html', {'error': error})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    return redirect('core:login')


@login_required
def dashboard(request):
    """Главная страница - дашборд"""
    
    # Получаем роль пользователя
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role')
    primary_role = user_roles.first()
    
    context = {
        'user_roles': user_roles,
        'primary_role': primary_role.role if primary_role else None,
        'timezone': timezone,
    }
    
    # Данные для менеджеров и выше
    if request.user.is_superuser or (primary_role and primary_role.role.code in ['OWNER', 'ADMIN', 'MANAGER']):
        # Статистика клиентов
        context['total_clients'] = Client.objects.filter(is_active=True).count()
        context['active_clients'] = Client.objects.filter(is_active=True, status='ACTIVE').count()
        context['silent_clients'] = Client.objects.filter(is_active=True, status='SILENT').count()
        context['lost_clients'] = Client.objects.filter(is_active=True, status='LOST').count()
        
        # Последние клиенты
        context['recent_clients'] = Client.objects.filter(is_active=True).order_by('-created_at')[:5]
        
        # Статистика платежей
        context['pending_payments'] = Payment.objects.filter(status='PENDING').count()
        context['today_payments'] = Payment.objects.filter(
            status='COMPLETED',
            paid_at__date=date.today()
        ).count()
        context['month_payments'] = Payment.objects.filter(
            status='COMPLETED',
            paid_at__month=timezone.now().month,
            paid_at__year=timezone.now().year
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Просроченные счета
        context['overdue_invoices'] = Invoice.objects.filter(
            status__in=['DRAFT', 'SENT'],
            due_date__lt=date.today()
        ).count()
        
        # Последние платежи
        context['recent_payments'] = Payment.objects.filter(status='COMPLETED').order_by('-paid_at')[:5]
        
        # Задачи
        context['my_tasks'] = Task.objects.filter(
            assigned_to=request.user,
            status__in=['TODO', 'IN_PROGRESS']
        ).count()
        context['overdue_tasks'] = Task.objects.filter(
            assigned_to=request.user,
            due_date__lt=date.today(),
            status__in=['TODO', 'IN_PROGRESS', 'REVIEW']
        ).count()
    
    # Данные для преподавателей
    if request.user.is_superuser or (primary_role and primary_role.role.code in ['OWNER', 'ADMIN', 'MANAGER', 'TEACHER']):
        try:
            employee_profile = request.user.profile
            context['my_lessons_today'] = Lesson.objects.filter(
                teacher=employee_profile,
                start_time__date=date.today()
            ).count()
            context['my_lessons_week'] = Lesson.objects.filter(
                teacher=employee_profile,
                start_time__week=timezone.now().week()
            ).count()
        except EmployeeProfile.DoesNotExist:
            context['my_lessons_today'] = 0
            context['my_lessons_week'] = 0
    
    # Недавние взаимодействия
    context['recent_interactions'] = Interaction.objects.filter(
        created_by=request.user
    ).order_by('-date_time')[:5]
    
    return render(request, 'dashboard.html', context)


@login_required
def client_list(request):
    """Список всех клиентов"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_view_clients:
        return redirect('core:dashboard')
    
    status = request.GET.get('status')
    search = request.GET.get('search', '')
    
    clients = Client.objects.filter(is_active=True)
    
    if status:
        clients = clients.filter(status=status)
    
    if search:
        clients = clients.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
        
    # Пагинация
    paginator = Paginator(clients.order_by('-created_at'), 25)
    page = request.GET.get('page')
    clients_page = paginator.get_page(page)
    
    context = {
        'clients': clients_page,
        'statuses': Client.STATUS_CHOICES,
        'current_status': status,
        'search_query': search,
    }
    
    return render(request, 'clients/client_list.html', context)


@login_required
def client_detail(request, client_id):
    """Детальная страница клиента"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_view_clients:
        return redirect('core:dashboard')
    
    client = get_object_or_404(Client, pk=client_id)
    
    # Получаем платежи и вычисляем общую сумму
    payments = client.payments.all().order_by('-created_at')
    total_payments = payments.aggregate(total=Sum('amount'))
    total_payments_amount = total_payments['total'] if total_payments['total'] else 0
    
    # Записи на курсы
    enrollments = client.enrollments.select_related('course', 'assigned_teacher').order_by('-created_at')
    active_enrollments = enrollments.filter(status='ACTIVE')
    
    # Контактные лица
    contacts = client.additional_contacts.all()
    
    # Фильтр для лога
    log_filter = request.GET.get('filter', 'all')  # all, comment, task, lesson
    
    # Взаимодействия
    interactions = client.interactions.all().order_by('-date_time')
    
    # Задачи для клиента
    tasks = Task.objects.filter(client=client).order_by('-created_at')
    
    # Занятия
    lessons = client.lessons.all().order_by('-start_time')
    
    # Объединяем в один поток для чата
    log_entries = []
    
    for interaction in interactions:
        log_entries.append({
            'type': 'interaction',
            'subtype': interaction.interaction_type.name.lower() if interaction.interaction_type else 'comment',
            'date_time': interaction.date_time,
            'subject': interaction.subject,
            'note': interaction.note,
            'created_by': interaction.created_by,
            'id': interaction.id,
        })
    
    for task in tasks:
        log_entries.append({
            'type': 'task',
            'subtype': 'task',
            'date_time': task.created_at,
            'subject': task.title,
            'note': task.description or '',
            'created_by': task.created_by,
            'status': task.status,
            'priority': task.priority,
            'id': task.id,
        })
    
    for lesson in lessons:
        log_entries.append({
            'type': 'lesson',
            'subtype': lesson.lesson_type.name if lesson.lesson_type else 'Занятие',
            'date_time': lesson.start_time,
            'subject': f"{lesson.lesson_type.name if lesson.lesson_type else 'Занятие'} с клиентом",
            'note': f"Преподаватель: {lesson.teacher.user.get_full_name() if lesson.teacher else '-'}",
            'status': lesson.status,
            'id': lesson.id,
        })
    
    # Сортируем по дате (старые сверху, новые снизу - как в чате)
    log_entries.sort(key=lambda x: x['date_time'])
    
    # Применяем фильтр
    if log_filter == 'comment':
        log_entries = [e for e in log_entries if e['type'] == 'interaction' and e['subtype'] == 'comment']
    elif log_filter == 'task':
        log_entries = [e for e in log_entries if e['type'] == 'task']
    elif log_filter == 'lesson':
        log_entries = [e for e in log_entries if e['type'] == 'lesson']
    
    # Ограничиваем количество
    log_entries = log_entries[:50]
    
    # Вычисляем остаток занятий и практики
    total_remaining_lessons = sum(e.remaining_lessons for e in active_enrollments)
    total_remaining_practice = sum(
        e.remaining_practice_hours for e in active_enrollments 
        if not e.is_unlimited_practice
    )
    
    context = {
        'client': client,
        'interactions': interactions,
        'payments': payments[:5],
        'lessons': lessons[:10],
        'enrollments': enrollments[:10],
        'active_enrollments': active_enrollments,
        'contacts': contacts,
        'tasks': tasks,
        'total_payments_amount': total_payments_amount,
        'total_remaining_lessons': total_remaining_lessons,
        'total_remaining_practice': total_remaining_practice,
        'log_entries': log_entries,
        'log_filter': log_filter,
        'call_count': interactions.filter(interaction_type__name__iexact='call').count(),
        'completed_tasks_count': tasks.filter(status='COMPLETED').count(),
    }
    
    return render(request, 'clients/client_detail.html', context)


@login_required
def create_interaction(request, client_id):
    """Создание взаимодействия через AJAX"""
    if request.method != 'POST':
        return redirect('core:client_detail', client_id=client_id)
    
    client = get_object_or_404(Client, pk=client_id)
    
    # Получаем тип взаимодействия из форм данных
    interaction_type_name = request.POST.get('type', 'comment')
    
    # Находим или создаем тип взаимодействия
    from interactions.models import InteractionType
    interaction_type, created = InteractionType.objects.get_or_create(
        name=interaction_type_name.capitalize(),
        defaults={'icon': '💬', 'color': '#00dbe9'}
    )
    
    content = request.POST.get('content', '')
    subject = request.POST.get('subject', '')
    
    if not content and not subject:
        return redirect('core:client_detail', client_id=client_id)
    
    # Создаем взаимодействие
    interaction = Interaction.objects.create(
        client=client,
        interaction_type=interaction_type,
        subject=subject or content[:50],
        note=content,
        date_time=timezone.now(),
        created_by=request.user,
        status='COMPLETED',
    )
    
    # Если это задача, создаем Task
    if interaction_type_name == 'task':
        Task.objects.create(
            title=subject or content[:100],
            client=client,
            assigned_to=request.user,
            due_date=timezone.now().date(),
            priority='MEDIUM',
        )
    
    return redirect('core:client_detail', client_id=client_id)


@login_required
def client_create(request):
    """Создание клиента"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_edit_clients:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        # Создаем клиента
        client = Client.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            middle_name=request.POST.get('middle_name', ''),
            phone=request.POST.get('phone'),
            email=request.POST.get('email', ''),
            status='POTENTIAL',
        )
        return redirect('core:client_detail', client_id=client.pk)
    
    return render(request, 'clients/client_form.html', {'action': 'create'})


@login_required
def client_update(request, client_id):
    """Редактирование клиента"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_edit_clients:
        return redirect('core:dashboard')
    
    client = get_object_or_404(Client, pk=client_id)
    
    if request.method == 'POST':
        client.first_name = request.POST.get('first_name')
        client.last_name = request.POST.get('last_name')
        client.middle_name = request.POST.get('middle_name', '')
        client.phone = request.POST.get('phone')
        client.email = request.POST.get('email', '')
        client.status = request.POST.get('status', 'ACTIVE')
        client.save()
        return redirect('core:client_detail', client_id=client.pk)
    
    return render(request, 'clients/client_form.html', {'action': 'update', 'client': client})


@login_required
def client_delete(request, client_id):
    """Удаление клиента (мягкое)"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_edit_clients:
        return redirect('core:dashboard')
    
    client = get_object_or_404(Client, pk=client_id)
    client.is_active = False
    client.save()
    
    return redirect('core:client_list')


@login_required
def payments_list(request):
    """Список платежей"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_view_finance:
        return redirect('core:dashboard')
    
    # Фильтры
    status = request.GET.get('status')
    client_id = request.GET.get('client_id')
    method_id = request.GET.get('method_id')
    payment_type = request.GET.get('payment_type')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    payments = Payment.objects.select_related('client', 'method', 'enrollment', 'contract').all()
    
    # Применяем фильтры
    if status:
        payments = payments.filter(status=status)
    
    if client_id:
        payments = payments.filter(client_id=client_id)
    
    if method_id:
        payments = payments.filter(method_id=method_id)
    
    if payment_type:
        payments = payments.filter(payment_type=payment_type)
    
    if search:
        payments = payments.filter(
            Q(invoice_number__icontains=search) |
            Q(description__icontains=search) |
            Q(client__last_name__icontains=search) |
            Q(client__first_name__icontains=search) |
            Q(client__phone__icontains=search)
        )
    
    if date_from:
        from datetime import datetime
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            payments = payments.filter(created_at__date__gte=date_from_obj)
        except (ValueError, TypeError):
            pass
    
    if date_to:
        from datetime import datetime
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            payments = payments.filter(created_at__date__lte=date_to_obj)
        except (ValueError, TypeError):
            pass
    
    # Сортировка по дате создания (новые сверху)
    payments = payments.order_by('-created_at')
    
    # Статистика для дашборда
    total_amount = payments.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    pending_amount = payments.filter(status='PENDING').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Средний чек
    completed_payments = payments.filter(status='COMPLETED')
    if completed_payments.exists():
        average_amount = completed_payments.aggregate(avg=Sum('amount'))['avg'] / completed_payments.count()
    else:
        average_amount = Decimal('0.00')
    
    context = {
        'payments': payments,
        'statuses': Payment.STATUS_CHOICES,
        'payment_types': Payment.PAYMENT_TYPE_CHOICES,
        'current_status': status,
        'current_client': client_id,
        'current_method': method_id,
        'current_payment_type': payment_type,
        'search_query': search,
        'date_from': date_from,
        'date_to': date_to,
        'total_amount': total_amount,
        'pending_amount': pending_amount,
        'average_amount': average_amount,
        'clients': Client.objects.filter(is_active=True).order_by('last_name'),
        'methods': PaymentMethod.objects.filter(is_active=True).order_by('name'),
    }
    
    return render(request, 'payments/payment_list.html', context)


@login_required
def payment_create(request):
    """Создание платежа"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_edit_clients:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        client = get_object_or_404(Client, pk=client_id, is_active=True)
        
        amount = Decimal(request.POST.get('amount', 0))
        method_id = request.POST.get('method_id')
        payment_type = request.POST.get('payment_type', 'ONCE')
        description = request.POST.get('description', '')
        due_date_str = request.POST.get('due_date')
        
        # Парсим дату
        from datetime import datetime
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        except (ValueError, TypeError):
            due_date = None
        
        # Создаем платёж
        payment = Payment.objects.create(
            client=client,
            amount=amount,
            method_id=method_id,
            payment_type=payment_type,
            description=description,
            due_date=due_date,
            processed_by=request.user,
            status='PENDING',
        )
    
        # Если есть запись на курс, привязываем
        enrollment_id = request.POST.get('enrollment_id')
        if enrollment_id:
            payment.enrollment = get_object_or_404(Enrollment, pk=enrollment_id)
            payment.save()
        
        return redirect('core:payments_list')
    
    context = {
        'clients': Client.objects.filter(is_active=True).order_by('last_name'),
        'methods': PaymentMethod.objects.filter(is_active=True).order_by('name'),
        'payment_types': Payment.PAYMENT_TYPE_CHOICES,
        'action': 'create',
    }
    
    return render(request, 'payments/payment_form.html', context)


@login_required
def payment_detail(request, payment_id):
    """Детальная страница платежа"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_view_finance:
        return redirect('core:dashboard')
    
    payment = get_object_or_404(Payment.objects.select_related('client', 'method', 'enrollment', 'contract'), pk=payment_id)
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/payment_detail.html', context)


@login_required
def payment_update(request, payment_id):
    """Редактирование платежа"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_edit_clients:
        return redirect('core:dashboard')
    
    payment = get_object_or_404(Payment, pk=payment_id)
    
    if request.method == 'POST':
        payment.amount = Decimal(request.POST.get('amount', payment.amount))
        payment.method_id = request.POST.get('method_id')
        payment.payment_type = request.POST.get('payment_type', payment.payment_type)
        payment.description = request.POST.get('description', payment.description)
        payment.status = request.POST.get('status', payment.status)
        
        due_date_str = request.POST.get('due_date')
        if due_date_str:
            from datetime import datetime
            try:
                payment.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
        
        payment.save()
        return redirect('core:payment_detail', payment_id=payment.pk)
    
    context = {
        'payment': payment,
        'methods': PaymentMethod.objects.filter(is_active=True).order_by('name'),
        'payment_types': Payment.PAYMENT_TYPE_CHOICES,
        'statuses': Payment.STATUS_CHOICES,
        'action': 'update',
    }
    
    return render(request, 'payments/payment_form.html', context)


@login_required
def payment_delete(request, payment_id):
    """Удаление платежа"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_edit_clients:
        return redirect('core:dashboard')
    
    payment = get_object_or_404(Payment, pk=payment_id)
    
    if request.method == 'POST':
        payment_id = payment.pk
        payment.delete()
        return redirect('core:payments_list')
    
    return render(request, 'payments/payment_confirm_delete.html', {'payment': payment})


@login_required
def payment_pay(request, payment_id):
    """Отметить платёж как оплаченный"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_edit_clients:
        return redirect('core:dashboard')
    
    payment = get_object_or_404(Payment, pk=payment_id)
    
    if request.method == 'POST':
        payment.status = 'COMPLETED'
        payment.paid_at = timezone.now()
        payment.paid_amount = payment.amount
        payment.save()
        return redirect('core:payment_detail', payment_id=payment.pk)
    
    return render(request, 'payments/payment_pay.html', {'payment': payment})


@login_required
def tasks_list(request):
    """Список задач"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_view_tasks:
        return redirect('core:dashboard')
    
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    
    # Если не суперпользователь и не менеджер, показываем только свои задачи
    if not request.user.is_superuser and user_roles and user_roles.role.code == 'TEACHER':
        tasks = Task.objects.filter(assigned_to=request.user)
    else:
        tasks = Task.objects.all()
    
    if status:
        tasks = tasks.filter(status=status)
    
    if priority:
        tasks = tasks.filter(priority=priority)
    
    context = {
        'tasks': tasks.order_by('-priority', 'due_date'),
        'statuses': Task.STATUS_CHOICES,
        'priorities': Task.PRIORITY_CHOICES,
        'current_status': status,
        'current_priority': priority,
    }
    
    return render(request, 'tasks/task_list.html', context)


@login_required
def schedule_view(request):
    """Расписание занятий с FullCalendar"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_view_schedule:
        return redirect('core:dashboard')
    
    # Фильтр по дате
    from datetime import timedelta
    date_str = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    
    try:
        # Парсим дату из строки
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        current_date = date.today()
    
    # Вычисляем предыдущий и следующий день
    previous_date = current_date - timedelta(days=1)
    next_date = current_date + timedelta(days=1)
    
    # Получаем занятия
    lessons = Lesson.objects.filter(
        start_time__date=current_date
    ).select_related('client', 'teacher', 'lesson_type').order_by('start_time')
    
    # Формируем события для FullCalendar
    events = []
    for lesson in lessons:
        # Цвет события в зависимости от статуса
        if lesson.status == 'COMPLETED':
            event_color = '#10b981'  # зелёный
        elif lesson.status == 'CANCELLED':
            event_color = '#ef4444'  # красный
        else:
            event_color = '#00dbe9'  # cyan (основной)
        
        event = {
            'id': str(lesson.id),
            'title': f"{lesson.lesson_type.name} • {lesson.client.last_name} {lesson.client.first_name[0]}.",
            'start': lesson.start_time.isoformat(),
            'end': lesson.end_time.isoformat() if lesson.end_time else None,
            'url': f"/dashboard/lessons/{lesson.id}/",
            'extendedProps': {
                'lessonId': lesson.id,
                'student': f"{lesson.client.last_name} {lesson.client.first_name}",
                'teacher': lesson.teacher.user.get_full_name() if lesson.teacher else "-",
                'room': lesson.room or "-",
                'status': lesson.get_status_display(),
                'lessonType': lesson.lesson_type.name if lesson.lesson_type else "-",
            },
            'color': event_color,
        }
        events.append(event)
    
    context = {
        'lessons': lessons,
        'current_date': current_date,
        'previous_date': previous_date.strftime('%Y-%m-%d'),
        'next_date': next_date.strftime('%Y-%m-%d'),
        'events': events,
    }
    
    return render(request, 'lessons/schedule.html', context)


# === КУРСЫ И ЗАПИСИ ===

@login_required
def courses_list(request):
    """Список курсов"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_view_clients:
        return redirect('core:dashboard')
    
    # Фильтры
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    courses = Course.objects.filter(is_active=True)
    
    if category:
        courses = courses.filter(category_id=category)
    
    if search:
        courses = courses.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    context = {
        'courses': courses.order_by('-is_popular', 'name'),
        'categories': CourseCategory.objects.filter(is_active=True),
        'current_category': category,
        'search_query': search,
    }
    
    return render(request, 'courses/course_list.html', context)


@login_required
def course_detail(request, course_id):
    """Детальная страница курса"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_view_clients:
        return redirect('core:dashboard')
    
    course = get_object_or_404(Course, pk=course_id, is_active=True)
    enrollments = course.enrollments.filter(status='ACTIVE').order_by('-created_at')
    
    context = {
        'course': course,
        'enrollments': enrollments[:20],
        'active_students': enrollments.count(),
        'available_slots': course.available_slots,
    }
    
    return render(request, 'courses/course_detail.html', context)


@login_required
def course_create(request):
    """Создание курса"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_manage_settings:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        course = Course.objects.create(
            name=request.POST.get('name'),
            slug=request.POST.get('slug'),
            category_id=request.POST.get('category') or None,
            description=request.POST.get('description'),
            full_description=request.POST.get('full_description'),
            duration=request.POST.get('duration'),
            total_lessons=int(request.POST.get('total_lessons', 12)),
            curriculum=request.POST.get('curriculum'),
            lesson_duration=int(request.POST.get('lesson_duration', 60)),
            base_price=Decimal(request.POST.get('base_price')),
            promo_price=Decimal(request.POST.get('promo_price')) if request.POST.get('promo_price') else None,
            is_active=request.POST.get('is_active') == 'on',
            is_popular=request.POST.get('is_popular') == 'on',
            materials_url=request.POST.get('materials_url', ''),
        )
        
        return redirect('core:courses_list')
    
    context = {
        'categories': CourseCategory.objects.filter(is_active=True),
        'durations': Course.DURATION_CHOICES,
        'action': 'create',
    }
    
    return render(request, 'courses/course_form.html', context)


@login_required
def course_update(request, course_id):
    """Редактирование курса"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_manage_settings:
        return redirect('core:dashboard')
    
    course = get_object_or_404(Course, pk=course_id)
    
    if request.method == 'POST':
        course.name = request.POST.get('name')
        course.slug = request.POST.get('slug')
        course.category_id = request.POST.get('category') or None
        course.description = request.POST.get('description')
        course.full_description = request.POST.get('full_description')
        course.duration = request.POST.get('duration')
        course.total_lessons = int(request.POST.get('total_lessons', 12))
        course.curriculum = request.POST.get('curriculum')
        course.lesson_duration = int(request.POST.get('lesson_duration', 60))
        course.base_price = Decimal(request.POST.get('base_price'))
        course.promo_price = Decimal(request.POST.get('promo_price')) if request.POST.get('promo_price') else None
        course.is_active = request.POST.get('is_active') == 'on'
        course.is_popular = request.POST.get('is_popular') == 'on'
        course.materials_url = request.POST.get('materials_url', '')
        course.save()
        
        return redirect('core:courses_list')
    
    context = {
        'course': course,
        'categories': CourseCategory.objects.filter(is_active=True),
        'durations': Course.DURATION_CHOICES,
        'action': 'update',
    }
    
    return render(request, 'courses/course_form.html', context)


@login_required
def enroll_client(request, course_id):
    """Запись клиента на курс"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_edit_clients:
        return redirect('core:dashboard')
    
    course = get_object_or_404(Course, pk=course_id, is_active=True)
    
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        client = get_object_or_404(Client, pk=client_id, is_active=True)
        
        # Преобразуем дату начала в объект date
        from datetime import datetime
        start_date_str = request.POST.get('start_date')
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            start_date = timezone.now().date()
        
        # Определение цены (акционная или базовая)
        enrolled_price = request.POST.get('enrolled_price')
        if not enrolled_price:
            enrolled_price = course.actual_price
        
        # Проверяем, есть ли уже запись
        existing_enrollment = Enrollment.objects.filter(
            course=course,
            client=client,
            start_date=start_date
        ).first()
        
        if existing_enrollment:
            # Обновляем существующую запись
            enrollment = existing_enrollment
            enrollment.total_lessons = course.total_lessons
            enrollment.total_practice_hours = 30
            enrollment.is_unlimited_practice = False
            enrollment.enrolled_price = Decimal(enrolled_price)
            enrollment.installment_type = request.POST.get('installment_type', 'NONE')
            enrollment.source = request.POST.get('source', '')
            enrollment.notes = request.POST.get('notes', '')
            enrollment.status = 'PENDING'
            enrollment.save()
        else:
            # Создаём новую запись
            enrollment = Enrollment.objects.create(
                course=course,
                client=client,
                start_date=start_date,
                total_lessons=course.total_lessons,
                total_practice_hours=30,
                is_unlimited_practice=False,
                enrolled_price=Decimal(enrolled_price),
                installment_type=request.POST.get('installment_type', 'NONE'),
                source=request.POST.get('source', ''),
                notes=request.POST.get('notes', ''),
                enrolled_by=request.user,
            )
        
        # Обновить статус клиента
        client.status = 'ACTIVE'
        client.save(update_fields=['status'])
        
        # Создать задачу только если это новая запись
        if not existing_enrollment:
            Task.objects.create(
                title=f'Начать занятия с {client.last_name} {client.first_name}',
                client=client,
                assigned_to=request.user,
                due_date=start_date,
                priority='MEDIUM',
            )
        
        return redirect('core:client_detail', client_id=client.pk)
    
    # Поиск клиентов
    search = request.GET.get('search', '')
    clients = Client.objects.filter(is_active=True)
    if search:
        clients = clients.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    context = {
        'course': course,
        'clients': clients[:20],
        'search_query': search,
        'start_date': timezone.now().date(),
        'action': 'enroll',
    }
    
    return render(request, 'courses/enroll_form.html', context)


@login_required
def enrollments_list(request):
    """Список всех записей на курсы"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_view_clients:
        return redirect('core:dashboard')
    
    status = request.GET.get('status')
    client_id = request.GET.get('client_id')
    
    enrollments = Enrollment.objects.select_related('course', 'client', 'assigned_teacher').all()
    
    if status:
        enrollments = enrollments.filter(status=status)
    
    if client_id:
        enrollments = enrollments.filter(client_id=client_id)
    
    context = {
        'enrollments': enrollments.order_by('-created_at'),
        'statuses': Enrollment.STATUS_CHOICES,
        'current_status': status,
        'current_client': client_id,
    }
    
    return render(request, 'courses/enrollment_list.html', context)


@login_required
def enrollment_detail(request, enrollment_id):
    """Детальная страница записи"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_view_clients:
        return redirect('core:dashboard')
    
    enrollment = get_object_or_404(Enrollment, pk=enrollment_id)
    
    context = {
        'enrollment': enrollment,
        'payments': enrollment.payments.all().order_by('-created_at'),
    }
    
    return render(request, 'courses/enrollment_detail.html', context)


# === ЛИЧНЫЙ КАБИНЕТ СТУДЕНТА ===

@login_required
def student_dashboard(request):
    """Личный кабинет студента"""
    
    # Получаем активные записи студента
    enrollments = Enrollment.objects.filter(
        client__user=request.user,
        status='ACTIVE'
    ).select_related('course', 'assigned_teacher').order_by('-created_at')
    
    # Предстоящие занятия
    from datetime import timedelta
    now = timezone.now()
    upcoming_lessons = Lesson.objects.filter(
        client__user=request.user,
        start_time__gte=now,
        status__in=['planned', 'rescheduled']
    ).select_related('lesson_type', 'teacher').order_by('start_time')[:5]
    
    # Последние занятия
    recent_lessons = Lesson.objects.filter(
        client__user=request.user,
        start_time__lt=now,
        status='completed'
    ).select_related('lesson_type', 'teacher').order_by('-start_time')[:5]
    
    # Неоплаченные платежи
    unpaid_payments = Payment.objects.filter(
        client__user=request.user,
        status='PENDING'
    ).order_by('due_date')[:3]
    
    context = {
        'enrollments': enrollments,
        'upcoming_lessons': upcoming_lessons,
        'recent_lessons': recent_lessons,
        'unpaid_payments': unpaid_payments,
        'total_active_courses': enrollments.count(),
    }
    
    return render(request, 'students/student_dashboard.html', context)


@login_required
def student_lessons(request):
    """Расписание занятий студента"""
    
    # Фильтры
    status = request.GET.get('status', 'upcoming')
    
    now = timezone.now()
    
    if status == 'upcoming':
        lessons = Lesson.objects.filter(
            client__user=request.user,
            start_time__gte=now
        ).select_related('lesson_type', 'teacher', 'enrollment').order_by('start_time')
    elif status == 'past':
        lessons = Lesson.objects.filter(
            client__user=request.user,
            start_time__lt=now,
            status='completed'
        ).select_related('lesson_type', 'teacher', 'enrollment').order_by('-start_time')
    elif status == 'cancelled':
        lessons = Lesson.objects.filter(
            client__user=request.user,
            status='cancelled'
        ).select_related('lesson_type', 'enrollment').order_by('-start_time')
    else:
        lessons = Lesson.objects.filter(
            client__user=request.user
        ).select_related('lesson_type', 'teacher', 'enrollment').order_by('-start_time')
    
    context = {
        'lessons': lessons,
        'current_status': status,
    }
    
    return render(request, 'students/student_lessons.html', context)


@login_required
def student_payments(request):
    """Платежи студента"""
    
    status = request.GET.get('status')
    
    payments = Payment.objects.filter(client__user=request.user)
    
    if status:
        payments = payments.filter(status=status)
    
    context = {
        'payments': payments.order_by('-created_at'),
        'statuses': Payment.STATUS_CHOICES,
        'current_status': status,
    }
    
    return render(request, 'students/student_payments.html', context)


@login_required
def student_progress(request, enrollment_id):
    """Прогресс студента по курсу"""
    
    enrollment = get_object_or_404(Enrollment, pk=enrollment_id, client__user=request.user)
    
    # Пересчитать прогресс
    enrollment.update_progress()
    
    # Все занятия
    lessons = enrollment.lessons.select_related('lesson_type', 'marked_by').order_by('-start_time')
    
    context = {
        'enrollment': enrollment,
        'lessons': lessons,
        'progress': enrollment.progress_percentage,
        'remaining_lessons': enrollment.remaining_lessons,
        'remaining_practice': enrollment.remaining_practice_hours,
    }
    
    return render(request, 'students/student_progress.html', context)


# === ДАШБОРД ПРЕПОДАВАТЕЛЯ ===

@login_required
def teacher_dashboard(request):
    """Дашборд преподавателя"""
    
    # Проверяем, есть ли профиль сотрудника
    try:
        teacher_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        # Если нет профиля, показываем базовый дашборд
        return redirect('core:dashboard')
    
    today = timezone.now().date()
    now = timezone.now()
    
    # Занятия сегодня
    lessons_today = Lesson.objects.filter(
        teacher=teacher_profile,
        start_time__date=today
    ).select_related('client', 'lesson_type').order_by('start_time')
    
    # Занятия на этой неделе
    lessons_this_week = Lesson.objects.filter(
        teacher=teacher_profile,
        start_time__week=now.isocalendar()[1],
        start_time__year=now.isocalendar()[0]
    ).select_related('client', 'lesson_type').order_by('start_time')
    
    # Активные студенты
    active_students_count = Enrollment.objects.filter(
        assigned_teacher=teacher_profile,
        status='ACTIVE'
    ).distinct('client').count()
    
    # Занятия для отмены/планирования
    upcoming_lessons = Lesson.objects.filter(
        teacher=teacher_profile,
        start_time__gte=now,
        status='planned'
    ).select_related('client', 'lesson_type').order_by('start_time')[:10]
    
    context = {
        'teacher_profile': teacher_profile,
        'lessons_today': lessons_today,
        'lessons_this_week': lessons_this_week,
        'lessons_today_count': lessons_today.count(),
        'lessons_week_count': lessons_this_week.count(),
        'active_students': active_students_count,
        'upcoming_lessons': upcoming_lessons,
        'today': today,
    }
    
    return render(request, 'teachers/teacher_dashboard.html', context)


@login_required
def teacher_schedule(request):
    """Расписание преподавателя"""
    
    try:
        teacher_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        return redirect('core:dashboard')
    
    date_str = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
    
    try:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        current_date = timezone.now().date()
    
    # Занятия на выбранную дату
    lessons = Lesson.objects.filter(
        teacher=teacher_profile,
        start_time__date=current_date
    ).select_related('client', 'lesson_type', 'enrollment').order_by('start_time')
    
    context = {
        'teacher_profile': teacher_profile,
        'lessons': lessons,
        'current_date': current_date,
    }
    
    return render(request, 'teachers/teacher_schedule.html', context)


@login_required
def teacher_students(request):
    """Список студентов преподавателя"""
    
    try:
        teacher_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        return redirect('core:dashboard')
    
    status = request.GET.get('status', 'ACTIVE')
    
    enrollments = Enrollment.objects.filter(
        assigned_teacher=teacher_profile,
        status=status
    ).select_related('client', 'course').order_by('client__last_name')
    
    context = {
        'teacher_profile': teacher_profile,
        'enrollments': enrollments,
        'statuses': Enrollment.STATUS_CHOICES,
        'current_status': status,
    }
    
    return render(request, 'teachers/teacher_students.html', context)


@login_required
def teacher_lesson_mark(request, lesson_id):
    """Отметить проведённое занятие"""
    
    try:
        teacher_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        return redirect('core:dashboard')
    
    lesson = get_object_or_404(Lesson, pk=lesson_id, teacher=teacher_profile)
    
    if request.method == 'POST':
        lesson.status = 'completed'
        lesson.marked_by = request.user
        lesson.marked_at = timezone.now()
        lesson.duration_minutes = int(request.POST.get('duration_minutes', lesson.duration_minutes or 60))
        
        # Если это практика, установить lesson_type_detail
        if lesson.lesson_type_detail == 'PRACTICE':
            lesson.teacher = None
        
        lesson.save()
        
        # Обновить прогресс записи
        if lesson.enrollment:
            lesson.enrollment.update_progress()
        
        return redirect('teacher:dashboard')
    
    context = {
        'lesson': lesson,
    }
    
    return render(request, 'teachers/lesson_mark.html', context)


# === ПАНЕЛЬ МЕНЕДЖЕРА ===

@login_required
def manager_dashboard(request):
    """Дашборд менеджера"""
    
    today = timezone.now().date()
    now = timezone.now()
    
    # Статистика клиентов
    total_clients = Client.objects.filter(is_active=True).count()
    active_clients = Client.objects.filter(is_active=True, status='ACTIVE').count()
    silent_clients = Client.objects.filter(is_active=True, status='SILENT').count()
    lost_clients = Client.objects.filter(is_active=True, status='LOST').count()
    
    # Активные записи
    active_enrollments = Enrollment.objects.filter(status='ACTIVE').count()
    pending_enrollments = Enrollment.objects.filter(status='PENDING').count()
    
    # Платежи
    pending_payments = Payment.objects.filter(status='PENDING').count()
    today_revenue = Payment.objects.filter(
        status='COMPLETED',
        paid_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    month_revenue = Payment.objects.filter(
        status='COMPLETED',
        paid_at__month=now.month,
        paid_at__year=now.year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Просроченные платежи
    overdue_payments = Payment.objects.filter(
        status='PENDING',
        due_date__lt=today
    ).count()
    
    # Задачи
    pending_tasks = Task.objects.filter(
        status__in=['TODO', 'IN_PROGRESS']
    ).count()
    overdue_tasks = Task.objects.filter(
        status__in=['TODO', 'IN_PROGRESS'],
        due_date__lt=today
    ).count()
    
    # Последние действия
    recent_enrollments = Enrollment.objects.select_related('client', 'course').order_by('-created_at')[:5]
    recent_payments = Payment.objects.select_related('client').order_by('-created_at')[:5]
    
    context = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'silent_clients': silent_clients,
        'lost_clients': lost_clients,
        'active_enrollments': active_enrollments,
        'pending_enrollments': pending_enrollments,
        'pending_payments': pending_payments,
        'today_revenue': today_revenue,
        'month_revenue': month_revenue,
        'overdue_payments': overdue_payments,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_enrollments': recent_enrollments,
        'recent_payments': recent_payments,
        'today': today,
    }
    
    return render(request, 'managers/manager_dashboard.html', context)


@login_required
def manager_clients_quick(request):
    """Быстрое управление клиентами для менеджера"""
    
    status = request.GET.get('status')
    search = request.GET.get('search', '')
    
    clients = Client.objects.filter(is_active=True)
    
    if status:
        clients = clients.filter(status=status)
    
    if search:
        clients = clients.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search)
        )
    
    context = {
        'clients': clients.order_by('-created_at')[:50],
        'statuses': Client.STATUS_CHOICES,
        'current_status': status,
        'search_query': search,
    }
    
    return render(request, 'managers/manager_clients.html', context)


@login_required
def manager_enrollments_quick(request):
    """Быстрое управление записями для менеджера"""
    
    status = request.GET.get('status')
    
    enrollments = Enrollment.objects.select_related('client', 'course', 'assigned_teacher')
    
    if status:
        enrollments = enrollments.filter(status=status)
    
    context = {
        'enrollments': enrollments.order_by('-created_at')[:50],
        'statuses': Enrollment.STATUS_CHOICES,
        'current_status': status,
    }
    
    return render(request, 'managers/manager_enrollments.html', context)


@login_required
def manager_payments_quick(request):
    """Быстрые платежи для менеджера"""
    
    status = request.GET.get('status')
    
    payments = Payment.objects.select_related('client', 'method')
    
    if status:
        payments = payments.filter(status=status)
    
    context = {
        'payments': payments.order_by('-created_at')[:50],
        'statuses': Payment.STATUS_CHOICES,
        'current_status': status,
    }
    
    return render(request, 'managers/manager_payments.html', context)


# === НАСТРОЙКИ ===

@login_required
def settings_view(request):
    """Главная страница настроек"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_manage_settings:
        return redirect('core:dashboard')
    
    # Статистика для панели
    tariffs_count = Tariff.objects.filter(is_active=True).count()
    courses_count = Course.objects.filter(is_active=True).count()
    clients_count = Client.objects.filter(is_active=True).count()
    
    context = {
        'tariffs_count': tariffs_count,
        'courses_count': courses_count,
        'clients_count': clients_count,
    }
    
    return render(request, 'settings/settings.html', context)


@login_required
def tariffs_list(request):
    """Список тарифов"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_manage_settings:
        return redirect('core:dashboard')
    
    category = request.GET.get('category')
    
    tariffs = Tariff.objects.all()
    
    if category:
        tariffs = tariffs.filter(category=category)
    
    context = {
        'tariffs': tariffs.order_by('weight', 'name'),
        'categories': Tariff.CATEGORY_CHOICES,
        'current_category': category,
    }
    
    return render(request, 'settings/tariffs_list.html', context)


@login_required
def tariff_create(request):
    """Создание тарифа"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_manage_settings:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        tariff = Tariff.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
            price=Decimal(request.POST.get('price')),
            lesson_count=int(request.POST.get('lesson_count')) if request.POST.get('lesson_count') else None,
            duration_days=int(request.POST.get('duration_days', 30)),
            category=request.POST.get('category', 'individual'),
            is_active=request.POST.get('is_active') == 'on',
            weight=int(request.POST.get('weight', 0)),
            discount_percent=Decimal(request.POST.get('discount_percent', 0)),
        )
        
        return redirect('core:tariffs_list')
    
    context = {
        'categories': Tariff.CATEGORY_CHOICES,
        'action': 'create',
    }
    
    return render(request, 'settings/tariff_form.html', context)


@login_required
def tariff_update(request, tariff_id):
    """Редактирование тарифа"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_manage_settings:
        return redirect('core:dashboard')
    
    tariff = get_object_or_404(Tariff, pk=tariff_id)
    
    if request.method == 'POST':
        tariff.name = request.POST.get('name')
        tariff.description = request.POST.get('description', '')
        tariff.price = Decimal(request.POST.get('price'))
        tariff.lesson_count = int(request.POST.get('lesson_count')) if request.POST.get('lesson_count') else None
        tariff.duration_days = int(request.POST.get('duration_days', 30))
        tariff.category = request.POST.get('category', 'individual')
        tariff.is_active = request.POST.get('is_active') == 'on'
        tariff.weight = int(request.POST.get('weight', 0))
        tariff.discount_percent = Decimal(request.POST.get('discount_percent', 0))
        tariff.save()
        
        return redirect('core:tariffs_list')
    
    context = {
        'tariff': tariff,
        'categories': Tariff.CATEGORY_CHOICES,
        'action': 'update',
    }
    
    return render(request, 'settings/tariff_form.html', context)


@login_required
def tariff_delete(request, tariff_id):
    """Удаление тарифа (мягкое)"""
    
    user_roles = RoleAssignment.objects.filter(user=request.user, is_primary=True).select_related('role').first()
    
    # Проверка прав
    if not request.user.is_superuser and user_roles and not user_roles.role.can_manage_settings:
        return redirect('core:dashboard')
    
    tariff = get_object_or_404(Tariff, pk=tariff_id)
    
    if request.method == 'POST':
        tariff.is_active = False
        tariff.save()
        return redirect('core:tariffs_list')
    
    return render(request, 'settings/tariff_confirm_delete.html', {'tariff': tariff})

