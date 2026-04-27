from django.shortcuts import render
from django.utils import timezone
from datetime import date, timedelta
from django.db import models
from products.models import Enrollment, Payment # Task, 
from clients.models import Client
from django.http import HttpResponse, JsonResponse

def get_product_details(request):
    return JsonResponse({"error": "Детали продукта — в разработке"})

def create_enrollment(request):
    return HttpResponse("Добавление продукта клиенту — в разработке")

def manager_dashboard(request):
    today = date.today()
    user = request.user

    # === СТАТИСТИКА ===
    trials_today = Enrollment.objects.filter(
        #client__manager=user,
        product__product_type='trial',
        start_date=today
    ).count()
    trial_plan = 10

    enrollments_today = Enrollment.objects.filter(
        #client__manager=user,
        start_date=today
    ).exclude(product__product_type='trial').count()
    enrollment_plan = 50

    sales_today = sum(
        e.price for e in Enrollment.objects.filter(
            #client__manager=user,
            created_at__date=today
        )
    )
    sales_plan = 200_000

    expected_payments = Payment.objects.filter(
        #enrollment__client__manager=user,
        is_paid=False,
        due_date__lte=today + timedelta(days=3)
    ).aggregate(total=models.Sum('amount_paid_by_client'))['total'] or 0

    # === ЗАДАЧИ (из ленты) ===
    from clients.models import Interaction
    tasks = Interaction.objects.filter(
        interaction_type='task',
        assigned_to=user,
        is_completed=False
    )
    overdue_tasks = tasks.filter(deadline__lt=today)
    today_tasks = tasks.filter(deadline=today)
    upcoming_tasks = tasks.filter(deadline__gt=today)

    # === ПРЕДУПРЕЖДЕНИЯ ===
    alerts = []

    # 1. Просроченные платежи
    overdue_payments = Payment.objects.filter(
        #enrollment__client__manager=user,
        is_paid=False,
        due_date__lt=today
    ).select_related('enrollment__client')
    for p in overdue_payments:
        days = (today - p.due_date).days
        alerts.append(f"Платёж от {p.enrollment.client} просрочен на {days} дн.")

    # 8. Новые лиды без пробника (>2 дней)
    new_leads = Client.objects.filter(
        #manager=user,
        created_at__date__lte=today - timedelta(days=2)
    ).exclude(enrollment__product__product_type='trial')
    for lead in new_leads:
        days = (today - lead.created_at.date()).days
        alerts.append(f"ЛИД УПУЩЕН: {lead} — без пробника {days} дней")

    alerts = alerts[:5]

    # Проценты для прогресс-баров
    def safe_percent(part, total):
        return int(part / total * 100) if total > 0 else 0

    context = {
        'trials_today': trials_today,
        'trial_plan': trial_plan,
        'trial_percent': safe_percent(trials_today, trial_plan),

        'enrollments_today': enrollments_today,
        'enrollment_plan': enrollment_plan,
        'enrollment_percent': safe_percent(enrollments_today, enrollment_plan),

        'sales_today': sales_today,
        'sales_plan': sales_plan,
        'sales_percent': safe_percent(sales_today, sales_plan),

        'expected_payments': expected_payments,

        'overdue_tasks': overdue_tasks,
        'today_tasks': today_tasks,
        'upcoming_tasks': upcoming_tasks,

        'alerts': alerts,
    }
    return render(request, 'sales/manager_dashboard.html', context)
