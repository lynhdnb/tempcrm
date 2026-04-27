from django.contrib import admin
from .models import ClientCabinetProfile


@admin.register(ClientCabinetProfile)
class ClientCabinetProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_confirmed', 'registration_approved', 'created_at')
    list_filter = ('email_confirmed', 'registration_approved')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

