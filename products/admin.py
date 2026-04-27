from django.contrib import admin
from .models import Product, Enrollment, PaymentMethod, Payment


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'product_type', 
        'base_lessons', 
        'base_practices', 
        'unlimited_practice', 
        'default_price', 
        'is_archived'
    ]
    list_filter = ['product_type', 'unlimited_practice', 'is_archived']
    search_fields = ['name']
    list_editable = ['is_archived']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'client', 
        'product', 
        'lessons_total', 
        'lessons_used',
        'practices_total',
        'practices_used',
        'unlimited_practice',
        'price',
        'installment_parts',
        'is_paid',
        'status'
    ]
    list_filter = ['status', 'unlimited_practice', 'is_paid', 'product']
    search_fields = ['client__first_name', 'client__last_name', 'product__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Клиент и продукт', {
            'fields': ('client', 'product')
        }),
        ('Лимиты', {
            'fields': ('lessons_total', 'lessons_used', 'practices_total', 'practices_used', 'unlimited_practice', 'unlimited_end_date')
        }),
        ('Оплата', {
            'fields': ('price', 'is_paid', 'installment_parts')
        }),
        ('Статус', {
            'fields': ('status',)
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.installment_parts and not change:
            payment_method = PaymentMethod.objects.filter(payment_type='cash').first()
            method_id = payment_method.id if payment_method else None
            obj.create_installment_payments_and_tasks(
                payment_method_id=method_id,
                created_by_user=request.user
            )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'payment_type', 'commission_percent', 'commission_fixed']
    list_filter = ['payment_type']
    search_fields = ['name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'enrollment',
        'amount_paid_by_client',
        'amount_received',
        'payment_method_name',
        'is_paid',
        'due_date'
    ]
    list_filter = ['is_paid', 'payment_type', 'is_installment']
    search_fields = ['enrollment__client__first_name', 'enrollment__client__last_name']
    readonly_fields = ['created_at', 'updated_at']
