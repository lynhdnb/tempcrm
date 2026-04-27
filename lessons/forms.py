from django import forms
from django.core.exceptions import ValidationError
from .models import Lesson, Room
from clients.models import Client
from core.models import UserProfile

class LessonForm(forms.ModelForm):
    # Поле для выбора шаблона (не сохраняется в модель)
    template_type = forms.ChoiceField(
        choices=[
            ('lesson+practice', '📚 Занятие + Практика (2 ч)'),
            ('practice+practice', '🎧 Практика + Практика (2 ч)'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Тип сессии',
        initial='lesson+practice'
    )
    
    class Meta:
        model = Lesson
        fields = ['client', 'teacher', 'room', 'start_time', 'notes']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'room': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Поле teacher необязательное (для самостоятельной практики)
        self.fields['teacher'].required = False
        # Фильтруем только преподавателей
        self.fields['teacher'].queryset = UserProfile.objects.filter(role='teacher')
        # Сортируем клиентов по ФИО
        self.fields['client'].queryset = Client.objects.all().order_by('last_name', 'first_name')
        # Сортируем кабинеты
        self.fields['room'].queryset = Room.objects.all().order_by('name')
        
        # Если кабинет один — выбираем его по умолчанию
        if Room.objects.count() == 1:
            self.fields['room'].initial = Room.objects.first().pk

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        teacher = cleaned_data.get('teacher')
        room = cleaned_data.get('room')
        template_type = cleaned_data.get('template_type')
        
        # Округляем время до целых часов
        if start:
            start = start.replace(minute=0, second=0, microsecond=0)
            cleaned_data['start_time'] = start
        
        # Авто-расчёт времени окончания на основе шаблона
        if start and template_type:
            from datetime import timedelta
            duration = 2  # часа по умолчанию
            cleaned_data['end_time'] = start + timedelta(hours=duration)
            
            # Определяем тип занятия
            if template_type == 'lesson+practice':
                cleaned_data['lesson_type'] = 'lesson'
                # Для занятия с учителем — учитель обязателен
                if not teacher:
                    raise ValidationError('Выберите преподавателя для занятия с преподавателем.')
            elif template_type == 'practice+practice':
                cleaned_data['lesson_type'] = 'practice'
                # Для практики учитель не нужен
                cleaned_data['teacher'] = None

        if start and teacher:
            # Проверка пересечения по преподавателю
            # Исключаем отменённые занятия (они не занимают время)
            overlapping = Lesson.objects.filter(
                teacher=teacher,
                start_time__lt=cleaned_data['end_time'],
                end_time__gt=start
            ).exclude(status__in=['cancelled_early', 'no_show'])
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise ValidationError('Этот преподаватель уже занят в это время.')

        if start and room:
            # Проверка пересечения по кабинету
            # Исключаем отменённые занятия (они не занимают время)
            overlapping = Lesson.objects.filter(
                room=room,
                start_time__lt=cleaned_data['end_time'],
                end_time__gt=start
            ).exclude(status__in=['cancelled_early', 'no_show'])
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise ValidationError('Этот кабинет уже занят в это время.')

        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Применяем lesson_type из template_type
        template_type = self.cleaned_data.get('template_type')
        if template_type == 'lesson+practice':
            instance.lesson_type = 'lesson'
        elif template_type == 'practice+practice':
            instance.lesson_type = 'practice'
            instance.teacher = None
        
        # !!! ВАЖНО: Сохраняем end_time из cleaned_data
        if 'end_time' in self.cleaned_data:
            instance.end_time = self.cleaned_data['end_time']
        
        if commit:
            instance.save()
        
        return instance