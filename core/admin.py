from django.contrib import admin
from .models import Client, ContactPerson, EmployeeProfile

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'gender')
    search_fields = ('last_name', 'first_name', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'phone', 'relation', 'is_primary')
    list_filter = ('is_primary', 'relation')
    search_fields = ('name', 'client__last_name')

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'hire_date', 'instruments')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')