from django.contrib import admin
from .models import Role, RoleAssignment, Client, ContactPerson, EmployeeProfile, Course, Enrollment, CourseCategory, Room, Resource, RoomResource
from django.contrib.admin.views.main import ChangeList

# Кастомизация заголовка админки
admin.site.site_header = "DJ CRM Админка"
admin.site.site_title = "DJ CRM Admin"
admin.site.index_title = "Панель управления"


class RoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'can_view_clients', 'can_view_finance']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
    

class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_primary', 'expires_at', 'created_at']
    list_filter = ['role', 'is_primary']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at']


class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active', 'sort_order']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'slug']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}


class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'capacity', 'is_active', 'is_available']
    list_filter = ['type', 'is_active', 'is_available']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'type', 'capacity', 'description')
        }),
        ('Статус', {
            'fields': ('is_active', 'is_available')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'quantity', 'condition', 'is_active', 'is_available']
    list_filter = ['type', 'condition', 'is_active', 'is_available']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'type', 'quantity', 'description')
        }),
        ('Состояние и статус', {
            'fields': ('condition', 'is_active', 'is_available', 'rental_price')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class RoomResourceAdmin(admin.ModelAdmin):
    list_display = ['room', 'resource', 'quantity_in_room']
    list_filter = ['room', 'resource']
    search_fields = ['room__name', 'resource__name']


class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'total_lessons', 'actual_price', 'is_active', 'is_popular', 'actions_column']
    list_filter = ['is_active', 'is_popular', 'category', 'duration']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    class Media:
        css = {
            'all': ('admin/css/admin_actions.css',)
        }
        js = ('admin/js/admin_actions.js',)
    
    def actions_column(self, obj):
        return f'<div class="action-menu"><button class="action-menu-btn" type="button" aria-label="Меню">⋮</button><div class="action-menu-dropdown"><a href="/admin/core/course/{obj.id}/change/">Редактировать</a><a href="/admin/core/course/{obj.id}/delete/" class="delete-link" onclick="return confirm(\'Вы уверены, что хотите удалить этот курс? Это действие нельзя отменить.\')">Удалить</a></div></div>'
    actions_column.short_description = 'Действия'
    actions_column.allow_tags = True

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['client', 'course', 'start_date', 'status', 'payment_status', 'enrolled_price', 'get_progress']
    list_filter = ['status', 'payment_status', 'installment_type', 'course', 'start_date']
    search_fields = ['client__first_name', 'client__last_name', 'course__name']
    readonly_fields = ['created_at', 'updated_at', 'completed_practice_hours']

    def get_progress(self, obj):
        return f"{obj.progress_percentage}%"
    get_progress.short_description = 'Прогресс'
    
    def completed_practice_hours(self, obj):
        return f"{obj.completed_practice_minutes / 60:.1f} ч"
    completed_practice_hours.short_description = 'Отработано практики'
    

class ClientAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'phone', 'status', 'silent_days', 'is_active', 'actions_column']
    list_filter = ['status', 'is_active', 'gender']
    search_fields = ['first_name', 'last_name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at', 'silent_days']

    class Media:
        css = {
            'all': ('admin/css/admin_actions.css',)
        }
        js = ('admin/js/admin_actions.js',)
    
    def actions_column(self, obj):
        return f'<div class="action-menu"><button class="action-menu-btn" type="button" aria-label="Меню">⋮</button><div class="action-menu-dropdown"><a href="/admin/core/client/{obj.id}/change/">Редактировать</a><a href="/admin/core/client/{obj.id}/delete/" class="delete-link" onclick="return confirm(\'Вы уверены, что хотите удалить этого клиента? Это действие нельзя отменить.\')">Удалить</a></div></div>'
    actions_column.short_description = 'Действия'
    actions_column.allow_tags = True


class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'phone', 'relation', 'is_primary']
    list_filter = ['is_primary', 'client']
    search_fields = ['name', 'phone', 'client__first_name', 'client__last_name']


class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'primary_role', 'phone', 'instruments', 'is_active', 'is_on_leave']
    list_filter = ['primary_role', 'is_active', 'is_on_leave']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'instruments']
    readonly_fields = ['created_at', 'updated_at']


# Регистрируем все модели с кастомизацией
admin.site.register(Role, RoleAdmin)
admin.site.register(RoleAssignment, RoleAssignmentAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(ContactPerson, ContactPersonAdmin)
admin.site.register(EmployeeProfile, EmployeeProfileAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(CourseCategory, CourseCategoryAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Resource, ResourceAdmin)
admin.site.register(RoomResource, RoomResourceAdmin)