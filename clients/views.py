from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django import forms
from django.utils import timezone
from core.decorators import role_required
from .models import Client, Interaction, InteractionEdit
from products.models import Payment
from .forms import ClientForm, InteractionForm
from django.contrib.auth.models import User


@role_required(['owner', 'admin', 'manager'])
def client_list(request):
    clients = Client.objects.select_related('manager').all()
    return render(request, 'clients/client_list.html', {'clients': clients})


@role_required(['owner', 'admin', 'manager'])
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Клиент успешно создан.')
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'clients/client_form.html', {'form': form})


@role_required(['owner', 'admin', 'manager'])
def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    interactions = Interaction.objects.filter(client=client).select_related('created_by', 'assigned_to').order_by('-created_at')
    
    # Получаем все записи на курсы
    enrollments = client.enrollment_set.select_related('product').all()
    
    # Получаем все платежи через записи (сортируем по номеру рассрочки)
    payments = Payment.objects.filter(
        enrollment__client=client
    ).select_related('enrollment__product').order_by('installment_number')
    
    # === Активные задачи клиента ===
    active_tasks = Interaction.objects.filter(
        client=client,
        interaction_type='task',
        is_completed=False
    ).select_related('assigned_to').order_by('deadline')
    
    # === Занятия клиента (только 2 ключевых) ===
    from lessons.models import Lesson
    from django.utils import timezone
    
    # Ближайшее будущее занятие
    next_lesson = Lesson.objects.filter(
        client=client,
        status='scheduled',
        start_time__gte=timezone.now()
    ).select_related('teacher__user', 'room').order_by('start_time').first()
    
    # Последнее завершённое занятие
    last_lesson = Lesson.objects.filter(
        client=client,
        status='completed'
    ).select_related('teacher__user', 'room').order_by('-start_time').first()
    
    # Формируем превью: приоритет — будущее + прошлое, иначе — 2 последних
    if next_lesson and last_lesson:
        lessons_preview = [last_lesson, next_lesson]
    elif next_lesson:
        lessons_preview = [next_lesson]
    elif last_lesson:
        # Если нет будущих, берём 2 последних завершённых
        last_two = Lesson.objects.filter(
            client=client,
            status='completed'
        ).select_related('teacher__user', 'room').order_by('-start_time')[:2]
        lessons_preview = list(last_two)
    else:
        lessons_preview = []
    
    return render(request, 'clients/client_detail.html', {
        'client': client,
        'interactions': interactions,
        'enrollments': enrollments,
        'payments': payments,
        'active_tasks': active_tasks,
        'lessons_preview': lessons_preview,
        'next_lesson': next_lesson,
        'now': timezone.now(),
    })


@role_required(['owner', 'admin', 'manager'])
def client_edit(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Клиент успешно обновлён.')
            return redirect('client_detail', client_id=client.id)
    else:
        form = ClientForm(instance=client)
    return render(request, 'clients/client_form.html', {'form': form})


@role_required(['owner', 'admin', 'manager'])
def add_interaction(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = InteractionForm(request.POST)
        if form.is_valid():
            interaction = form.save(commit=False)
            interaction.client = client
            interaction.created_by = request.user
            interaction.save()
            messages.success(request, 'Взаимодействие добавлено.')
            return redirect('client_detail', client_id=client.id)
    # В случае GET или ошибки — возвращаем в карточку
    return redirect('client_detail', client_id=client.id)
    

@role_required(['owner', 'admin', 'manager'])
def add_note(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Interaction.objects.create(
                client=client,
                interaction_type='note',
                content=content,
                created_by=request.user
            )
            messages.success(request, 'Комментарий добавлен.')
        else:
            messages.warning(request, 'Комментарий не может быть пустым.')
        return redirect('client_detail', client_id=client.id)
    # Если GET — возвращаем в карточку (форма встроена в шаблон)
    return redirect('client_detail', client_id=client.id)


class TaskForm(forms.Form):
    content = forms.CharField(
        label='Текст задачи',
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        strip=True
    )
    deadline = forms.DateTimeField(
        label='Дедлайн',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        help_text='Обязательно укажите дату и время'
    )
    assigned_to = forms.ModelChoiceField(
        label='Назначить',
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label='Себе',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Исключаем текущего пользователя из списка (т.к. "Себе" — по умолчанию)
            self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).exclude(id=user.id)

    def clean_deadline(self):
        deadline = self.cleaned_data['deadline']
        if deadline <= timezone.now():
            raise forms.ValidationError('Дедлайн должен быть в будущем.')
        return deadline


@role_required(['owner', 'admin', 'manager'])
def add_task(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, current_user=request.user)
        if form.is_valid():
            assigned = form.cleaned_data['assigned_to'] or request.user
            Interaction.objects.create(
                client=client,
                interaction_type='task',
                content=form.cleaned_data['content'],
                deadline=form.cleaned_data['deadline'],
                assigned_to=assigned,
                is_reminder=True,
                created_by=request.user
            )
            messages.success(request, 'Задача создана.')
            return redirect('client_detail', client_id=client.id)
    else:
        form = TaskForm(current_user=request.user)

    return render(request, 'clients/task_form.html', {
        'client': client,
        'form': form,
        'title': 'Новая задача'
    })

@role_required(['owner', 'admin', 'manager'])
def edit_task(request, interaction_id):
    interaction = get_object_or_404(Interaction, id=interaction_id, interaction_type='task')
    client = interaction.client

    # Проверка прав: только автор или вышестоящие роли могут редактировать
    if interaction.created_by != request.user:
        user_role = request.user.profile.role
        creator_role = interaction.created_by.profile.role
        role_hierarchy = {'owner': 3, 'admin': 2, 'manager': 1}
        if role_hierarchy.get(user_role, 0) <= role_hierarchy.get(creator_role, 0):
            messages.error(request, 'У вас нет прав на редактирование этой задачи.')
            return redirect('client_detail', client_id=client.id)

    if request.method == 'POST':
        form = TaskForm(request.POST, current_user=request.user)
        if form.is_valid():
            interaction.content = form.cleaned_data['content']
            interaction.deadline = form.cleaned_data['deadline']
            interaction.assigned_to = form.cleaned_data['assigned_to'] or request.user
            interaction.save()
            messages.success(request, 'Задача обновлена.')
            return redirect('client_detail', client_id=client.id)
    else:
        # Заполняем форму текущими данными
        initial = {
            'content': interaction.content,
            'deadline': interaction.deadline,
            'assigned_to': interaction.assigned_to
        }
        form = TaskForm(initial=initial, current_user=request.user)

    return render(request, 'clients/task_form.html', {
        'client': client,
        'form': form,
        'title': 'Редактировать задачу'
    })

@role_required(['owner', 'admin', 'manager'])
def edit_note(request, interaction_id):
    interaction = get_object_or_404(Interaction, id=interaction_id, interaction_type='note')
    
    # Проверка: только автор может редактировать
    if interaction.created_by != request.user:
        messages.error(request, 'Только автор может редактировать комментарий.')
        return redirect('client_detail', client_id=interaction.client.id)

    if request.method == 'POST':
        new_content = request.POST.get('content', '').strip()
        if not new_content:
            messages.warning(request, 'Комментарий не может быть пустым.')
            return redirect('edit_note', interaction_id=interaction.id)
        
        # Сохраняем правку в историю
        InteractionEdit.objects.create(
            interaction=interaction,
            edited_by=request.user,
            old_content=interaction.content,
            new_content=new_content
        )
        
        # Обновляем текущий текст
        interaction.content = new_content
        interaction.is_edited = True
        interaction.save()
        
        messages.success(request, 'Комментарий обновлён.')
        return redirect('client_detail', client_id=interaction.client.id)
    
    return render(request, 'clients/note_edit.html', {
        'interaction': interaction,
        'client': interaction.client
    })
    
@role_required(['owner', 'admin', 'manager'])
def mark_task_completed(request, interaction_id):
    interaction = get_object_or_404(Interaction, id=interaction_id, interaction_type='task')

    # Проверка: только назначенный пользователь или вышестоящие могут завершить
    if interaction.assigned_to and interaction.assigned_to != request.user:
        user_role = request.user.profile.role
        assigned_role = interaction.assigned_to.profile.role
        role_hierarchy = {'owner': 3, 'admin': 2, 'manager': 1}
        if role_hierarchy.get(user_role, 0) <= role_hierarchy.get(assigned_role, 0):
            messages.error(request, 'Только назначенный пользователь или вышестоящие могут завершить задачу.')
            return redirect('client_detail', client_id=interaction.client.id)

    # === Если задача связана с занятием и нет данных формы — показываем форму ===
    if interaction.lesson and 'lesson_outcome' not in request.POST:
        # Показываем форму выбора статуса занятия
        return render(request, 'clients/task_complete_with_lesson.html', {
            'interaction': interaction,
            'lesson': interaction.lesson,
        })

    # === Обработка формы (POST с lesson_outcome) ===
    if request.method == 'POST' and interaction.lesson:
        lesson_outcome = request.POST.get('lesson_outcome', '')
        
        if lesson_outcome == 'confirmed':
            interaction.lesson.status = 'confirmed'
            interaction.lesson.status_changed_at = timezone.now()
            interaction.lesson.status_changed_by = request.user.profile
            interaction.lesson.save()
            messages.success(request, 'Занятие подтверждено. Клиент придёт.')
            
        elif lesson_outcome == 'completed':
            interaction.lesson.status = 'completed'
            interaction.lesson.status_changed_at = timezone.now()
            interaction.lesson.status_changed_by = request.user.profile
            interaction.lesson.save()
            messages.success(request, 'Занятие завершено. Баланс списан.')
            
        elif lesson_outcome == 'no_show':
            interaction.lesson.status = 'no_show'
            interaction.lesson.status_changed_at = timezone.now()
            interaction.lesson.status_changed_by = request.user.profile
            interaction.lesson.save()
            messages.success(request, 'Клиент не явился. Баланс списан.')
        
        interaction.is_completed = True
        interaction.save()
        
        return redirect('lesson_detail', pk=interaction.lesson.pk)

    # === Если задача не связана с занятием — просто завершаем ===
    interaction.is_completed = True
    interaction.save()
    messages.success(request, 'Задача отмечена как выполненная.')
    return redirect('client_detail', client_id=interaction.client.id)