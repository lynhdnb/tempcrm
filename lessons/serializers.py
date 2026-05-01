from rest_framework import serializers
from .models import Lesson

class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор для передачи данных занятия в FullCalendar"""
    title = serializers.SerializerMethodField()
    start = serializers.DateTimeField(source='start_time')
    end = serializers.DateTimeField(source='end_time', required=False)
    backgroundColor = serializers.SerializerMethodField()
    borderColor = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'start', 'end', 'backgroundColor', 'borderColor'] # Убрали 'description', если этого поля нет в модели Lesson

    def get_title(self, obj):
        # Формируем заголовок: "Клиент - Инструмент"
        client_name = f"{obj.client.last_name} {obj.client.first_name}"
        instrument = obj.lesson_type.name if obj.lesson_type else "Занятие"
        return f"{client_name} ({instrument})"

    def get_backgroundColor(self, obj):
        # Цвета для разных типов занятий (можно настроить)
        colors = {
            'Фортепиано': '#3788d8',
            'Гитара': '#28a745',
            'Вокал': '#dc3545',
            'Диджеинг': '#6f42c1',
        }
        if obj.lesson_type:
            return colors.get(obj.lesson_type.name, '#007bff')
        return '#007bff'

    def get_borderColor(self, obj):
        return self.get_backgroundColor(obj) # Граница того же цвета