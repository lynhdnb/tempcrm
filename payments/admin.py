from django.contrib import admin
from .models import PaymentMethod, PaymentPackage, Contract, Payment, Invoice


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'icon', 'is_active', 'commission_percentage']
    list_filter = ['is_active', 'requires_contract']
    search_fields = ['name', 'code']


@admin.register(PaymentPackage)
class PaymentPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'lesson_type', 'lesson_count', 'price', 'discount_percentage', 'is_active', 'is_popular']
    list_filter = ['is_active', 'is_popular', 'lesson_type']
    search_fields = ['name', 'slug']
    readonly_fields = ['price_per_lesson', 'discounted_price']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['contract_number', 'client', 'status', 'start_date', 'end_date', 'lesson_package']
    list_filter = ['status', 'start_date', 'lesson_package']
    search_fields = ['contract_number', 'client__first_name', 'client__last_name']
    readonly_fields = ['contract_number', 'created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('contract_number', 'client', 'start_date', 'end_date', 'status')
        }),
        ('Условия', {
            'fields': ('lesson_package', 'monthly_fee')
        }),
        ('Документы', {
            'fields': ('contract_file', 'notes'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['client', 'amount', 'status', 'method', 'payment_type', 'due_date', 'paid_at']
    list_filter = ['status', 'payment_type', 'method', 'due_date']
    search_fields = ['client__first_name', 'client__last_name', 'description', 'invoice_number']
    readonly_fields = ['created_at', 'updated_at', 'processed_by', 'remaining_amount', 'is_paid', 'is_overdue']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('client', 'contract', 'payment_type', 'amount', 'paid_amount', 'method')
        }),
        ('Статус', {
            'fields': ('status', 'due_date', 'paid_at')
        }),
        ('Детали', {
            'fields': ('description', 'invoice_number', 'notes'),
            'classes': ('collapse',)
        }),
        ('Возвраты', {
            'fields': ('refund_reason', 'refunded_at'),
            'classes': ('collapse',)
        }),
        ('Даты и обработчик', {
            'fields': ('processed_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'amount', 'status', 'due_date', 'issued_date']
    list_filter = ['status', 'issued_date', 'due_date']
    search_fields = ['invoice_number', 'client__first_name', 'client__last_name']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at', 'created_by', 'is_overdue']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('invoice_number', 'client', 'payment', 'amount')
        }),
        ('Даты', {
            'fields': ('due_date', 'issued_date', 'sent_at')
        }),
        ('Статус', {
            'fields': ('status', 'sent_to_email')
        }),
        ('Позиции', {
            'fields': ('items', 'description'),
            'classes': ('collapse',)
        }),
        ('Документы', {
            'fields': ('pdf_file', 'notes'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
