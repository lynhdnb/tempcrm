"""
Сериализаторы для API (аналог AlfaCRM)
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Client, ContactPerson, EmployeeProfile, 
    Course, CourseCategory, Enrollment,
    ClientComment, Room, Resource, Role, RoleAssignment, Tariff
)


class BaseAlfaSerializer(serializers.Serializer):
    """
    Базовый сериализатор с унифицированным форматом ответов
    
    Используется для формирования ответов в стиле AlfaCRM:
    - success: bool
    - errors: list
    - model: data
    - message: str (опционально)
    """
    
    def to_representation(self, instance):
        """Унифицированный формат вывода"""
        return super().to_representation(instance)
    
    @staticmethod
    def success_response(data, message=""):
        """Успешный ответ"""
        response = {
            "success": True,
            "errors": [],
            "model": data
        }
        if message:
            response["message"] = message
        return response
    
    @staticmethod
    def error_response(errors, message=""):
        """Ответ с ошибками"""
        return {
            "success": False,
            "errors": errors if isinstance(errors, list) else [errors],
            "message": message
        }
    
    @staticmethod
    def index_response(items, total, page=0, count=None):
        """Ответ для списка с пейджинацией"""
        return {
            "total": total,
            "count": count if count else len(items),
            "page": page,
            "items": items
        }


# ========================================
# Сериализаторы для Client
# ========================================

class ContactPersonSerializer(serializers.ModelSerializer):
    """Сериализатор контактного лица"""
    class Meta:
        model = ContactPerson
        fields = ['id', 'name', 'phone', 'relation', 'is_primary']


class ClientCommentSerializer(serializers.ModelSerializer):
    """Сериализатор комментария к клиенту"""
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ClientComment
        fields = [
            'id', 'client', 'user', 'author_name',
            'text', 'comment_type', 'is_internal', 'is_pinned',
            'reminder_date', 'reminder_sent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_author_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}" or obj.user.username
        return "Аноним"


class ClientBriefSerializer(serializers.ModelSerializer):
    """Краткая информация о клиенте"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = ['id', 'full_name', 'first_name', 'last_name', 'phone', 'email', 'status']
    
    def get_full_name(self, obj):
        parts = [obj.last_name, obj.first_name]
        if obj.middle_name:
            parts.append(obj.middle_name)
        return ' '.join(parts)


class ClientSerializer(serializers.ModelSerializer):
    """Полный сериализатор клиента"""
    full_name = serializers.SerializerMethodField()
    additional_contacts = ContactPersonSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    latest_comment = ClientCommentSerializer(read_only=True)
    assigned_manager_name = serializers.SerializerMethodField()
    age = serializers.IntegerField(read_only=True)
    total_balance = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = Client
        fields = [
            'id', 'first_name', 'last_name', 'middle_name', 'full_name',
            'gender', 'birth_date', 'age',
            'phone', 'email', 'address',
            'parent', 'source', 'notes', 'tags',
            'status', 'silent_days', 'last_interaction_date',
            'is_active', 'is_deleted',
            'assigned_manager', 'assigned_manager_name',
            'balance_contract', 'balance_bonus', 'total_balance',
            'lesson_count', 'last_attend_date', 'next_lesson_date',
            'first_payment_date', 'color',
            'additional_contacts', 'comments_count', 'latest_comment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'silent_days', 'comments_count', 'age', 'total_balance']
    
    def get_full_name(self, obj):
        parts = [obj.last_name, obj.first_name]
        if obj.middle_name:
            parts.append(obj.middle_name)
        return ' '.join(parts)
    
    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_assigned_manager_name(self, obj):
        if obj.assigned_manager:
            return f"{obj.assigned_manager.first_name} {obj.assigned_manager.last_name}" or obj.assigned_manager.username
        return None


# ========================================
# Сериализаторы для Course
# ========================================

class CourseCategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории курса"""
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_active']


class CourseBriefSerializer(serializers.ModelSerializer):
    """Краткая информация о курсе"""
    category_name = serializers.SerializerMethodField()
    actual_price_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'slug', 'category', 'category_name',
            'duration', 'total_lessons', 'base_price', 'promo_price',
            'actual_price_display', 'is_active', 'is_popular'
        ]
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    
    def get_actual_price_display(self, obj):
        price = obj.actual_price
        return f"{price} ₽" if price else "Цена не указана"


class CourseSerializer(serializers.ModelSerializer):
    """Полный сериализатор курса"""
    category = CourseCategorySerializer(read_only=True)
    active_enrollments_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'slug', 'category', 'description', 'full_description',
            'duration', 'total_lessons', 'lesson_duration', 'curriculum',
            'base_price', 'promo_price', 'actual_price',
            'materials_url', 'is_active', 'is_popular',
            'active_enrollments_count', 'available_slots',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'active_enrollments_count']


# ========================================
# Сериализаторы для Enrollment
# ========================================

class EnrollmentBriefSerializer(serializers.ModelSerializer):
    """Краткая информация о записи на курс"""
    course_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_name', 'client', 'client_name',
            'start_date', 'total_lessons', 'completed_lessons',
            'lessons_remaining', 'status', 'status_display',
            'payment_status', 'enrolled_price', 'paid_amount', 'remaining_amount',
            'progress_percentage', 'is_completed'
        ]
    
    def get_course_name(self, obj):
        return obj.course.name
    
    def get_client_name(self, obj):
        return f"{obj.client.last_name} {obj.client.first_name}"
    
    def get_status_display(self, obj):
        return obj.get_status_display()


class EnrollmentSerializer(serializers.ModelSerializer):
    """Полный сериализатор записи на курс"""
    course = CourseBriefSerializer(read_only=True)
    client = ClientBriefSerializer(read_only=True)
    assigned_teacher_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'client',
            'status', 'payment_status',
            'start_date',
            'total_lessons', 'total_practice_hours', 'is_unlimited_practice',
            'completed_lessons', 'completed_practice_minutes',
            'lessons_remaining', 'remaining_practice_hours',
            'progress_percentage', 'is_completed',
            'installment_type', 'enrolled_price', 'paid_amount', 'remaining_amount',
            'assigned_teacher', 'assigned_teacher_name',
            'notes', 'source', 'enrolled_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'completed_practice_minutes',
            'lessons_remaining', 'remaining_practice_hours',
            'progress_percentage', 'is_completed', 'remaining_amount',
            'assigned_teacher_name'
        ]
    
    def get_assigned_teacher_name(self, obj):
        if obj.assigned_teacher:
            return f"{obj.assigned_teacher.user.first_name} {obj.assigned_teacher.user.last_name}"
        return None


# ========================================
# Сериализаторы для EmployeeProfile
# ========================================

class EmployeeProfileBriefSerializer(serializers.ModelSerializer):
    """Краткая информация о сотруднике"""
    full_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeProfile
        fields = ['id', 'user', 'full_name', 'phone', 'instruments', 'role_name', 'is_active']
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
    def get_role_name(self, obj):
        return obj.primary_role.name if obj.primary_role else None


class EmployeeProfileSerializer(serializers.ModelSerializer):
    """Полный сериализатор профиля сотрудника"""
    user = serializers.SerializerMethodField()
    primary_role_name = serializers.SerializerMethodField()
    active_enrollments_count = serializers.SerializerMethodField()
    lessons_today_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'user', 'phone', 'bio', 'hire_date',
            'instruments', 'hourly_rate',
            'primary_role', 'primary_role_name',
            'can_manage_rooms', 'can_manage_resources',
            'is_active', 'is_on_leave', 'leave_end_date',
            'active_enrollments_count', 'lessons_today_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name
        }
    
    def get_primary_role_name(self, obj):
        return obj.primary_role.name if obj.primary_role else None
    
    def get_active_enrollments_count(self, obj):
        return obj.enrollments.filter(status='ACTIVE').count()
    
    def get_lessons_today_count(self, obj):
        from lessons.models import Lesson
        from datetime import date
        return Lesson.objects.filter(
            teacher=obj,
            start_time__date=date.today()
        ).count()


# ========================================
# Сериализаторы для Room и Resource
# ========================================

class RoomSerializer(serializers.ModelSerializer):
    """Сериализатор аудитории"""
    type_display = serializers.SerializerMethodField()
    resources_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = [
            'id', 'name', 'type', 'type_display', 'capacity', 'description',
            'is_active', 'is_available', 'resources_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_type_display(self, obj):
        return obj.get_type_display()
    
    def get_resources_count(self, obj):
        return obj.room_resources.count()


class ResourceSerializer(serializers.ModelSerializer):
    """Сериализатор ресурса"""
    type_display = serializers.SerializerMethodField()
    condition_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Resource
        fields = [
            'id', 'name', 'type', 'type_display', 'quantity', 'description',
            'condition', 'condition_display', 'is_active', 'is_available',
            'rental_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_type_display(self, obj):
        return obj.get_type_display()
    
    def get_condition_display(self, obj):
        return obj.get_condition_display()


# ========================================
# Сериализаторы для Role
# ========================================

class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор роли"""
    class Meta:
        model = Role
        fields = [
            'id', 'code', 'code_display', 'name', 'description',
            'can_view_clients', 'can_edit_clients',
            'can_view_finance', 'can_edit_finance',
            'can_view_schedule', 'can_edit_schedule',
            'can_view_tasks', 'can_create_tasks',
            'can_manage_users', 'can_view_reports',
            'can_manage_settings',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_code_display(self, obj):
        return obj.get_code_display()


class RoleAssignmentSerializer(serializers.ModelSerializer):
    """Сериализатор назначения роли"""
    user_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RoleAssignment
        fields = [
            'id', 'user', 'user_name', 'role', 'role_name',
            'is_primary', 'expires_at', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
    def get_role_name(self, obj):
        return obj.role.name


# ========================================
# Сериализаторы для ClientComment
# ========================================

class ClientCommentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания комментария"""
    class Meta:
        model = ClientComment
        fields = ['text', 'comment_type', 'is_internal', 'is_pinned', 'reminder_date']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ========================================
# Сериализаторы для Tariff
# ========================================

class TariffSerializer(serializers.ModelSerializer):
    """Сериализатор тарифа"""
    category_display = serializers.SerializerMethodField()
    price_per_lesson = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    is_unlimited = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Tariff
        fields = [
            'id', 'name', 'description', 'category', 'category_display',
            'price', 'lesson_count', 'duration_days', 'discount_percent',
            'price_per_lesson', 'is_unlimited', 'is_active', 'weight',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'price_per_lesson', 'is_unlimited']
    
    def get_category_display(self, obj):
        return obj.get_category_display()