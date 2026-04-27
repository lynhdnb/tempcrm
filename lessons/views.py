from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from core.decorators import role_required
from .models import Lesson
from .forms import LessonForm

@role_required(['owner', 'admin', 'manager'])
def lesson_list(request):
    lessons = Lesson.objects.select_related('client', 'teacher__user', 'room').all()
    
    client_id = request.GET.get('client')
    if client_id:
        lessons = lessons.filter(client_id=client_id)
    
    return render(request, 'lessons/lesson_list.html', {'lessons': lessons})

@role_required(['owner', 'admin', 'manager'])
def lesson_create(request):
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.created_by = request.user.profile  # ← Сохраняем создателя
            lesson.save()
            messages.success(request, 'Занятие успешно создано.')
            return redirect('lesson_list')
    else:
        form = LessonForm()
    return render(request, 'lessons/lesson_form.html', {'form': form})

@role_required(['owner', 'admin', 'manager'])
def lesson_update(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, 'Занятие успешно обновлено.')
            return redirect('lesson_list')
    else:
        form = LessonForm(instance=lesson)
    
    return render(request, 'lessons/lesson_form.html', {'form': form})

@role_required(['owner', 'admin', 'manager'])
def lesson_delete(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    
    if request.method == 'POST':
        cancel_type = request.POST.get('cancel_type', '')
        comment = request.POST.get('delete_comment', '')
        
        if not cancel_type:
            messages.error(request, 'Выберите тип отмены.')
            return redirect('lesson_delete', pk=pk)
        
        if not comment:
            messages.error(request, 'Необходимо указать причину.')
            return redirect('lesson_delete', pk=pk)
        
        # Устанавливаем статус в зависимости от выбора
        if cancel_type == 'no_show':
            lesson.status = 'no_show'
            status_message = 'Занятие отмечено как "Не явился"'
        elif cancel_type == 'cancelled_early':
            lesson.status = 'cancelled_early'
            status_message = 'Занятие отменено заранее'
        else:
            messages.error(request, 'Неверный тип отмены.')
            return redirect('lesson_delete', pk=pk)
        
        # Сохраняем комментарий и метаданные
        lesson.notes = f"[{status_message}] {comment}\n{lesson.notes}"
        lesson.status_changed_at = timezone.now()
        lesson.status_changed_by = request.user.profile
        lesson.save()
        
        messages.success(request, f'{status_message}.')
        return redirect('lesson_list')
    
    return render(request, 'lessons/lesson_confirm_delete.html', {'lesson': lesson})

@role_required(['owner', 'admin', 'manager'])
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    return render(request, 'lessons/lesson_detail.html', {'lesson': lesson})

# Календарь — доступен всем ролям (включая teacher)
@role_required(['owner', 'admin', 'manager', 'teacher'])
def calendar_view(request):
    return render(request, 'lessons/calendar.html')

@role_required(['owner', 'admin', 'manager', 'teacher'])
def lesson_events_api(request):
    lessons = Lesson.objects.select_related('client', 'teacher__user', 'room').all()
    
    # Если пользователь — учитель, показываем только его занятия
    if request.user.profile.role == 'teacher':
        lessons = lessons.filter(teacher=request.user.profile)
    
    events = []
    for lesson in lessons:
        events.append({
            'id': lesson.id,
            'title': f"{lesson.client.last_name} {lesson.client.first_name}",
            'start': lesson.start_time.isoformat(),
            'end': lesson.end_time.isoformat(),
            'extendedProps': {
                'teacher': f"{lesson.teacher.user.last_name} {lesson.teacher.user.first_name}" if lesson.teacher else 'Самостоятельная практика',
                'room': lesson.room.name,
                'notes': lesson.notes,
            }
        })
    return JsonResponse(events, safe=False)