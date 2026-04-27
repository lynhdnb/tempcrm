from django.contrib import admin
from .models import Client, Interaction

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'phone', 'email', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('last_name', 'first_name', 'phone', 'email')

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('client', 'interaction_type', 'created_by', 'created_at')
    list_filter = ('interaction_type', 'created_at')
    search_fields = ('client__last_name', 'client__first_name', 'content')