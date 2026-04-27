from django import forms
from products.models import Enrollment, Product, PaymentMethod

class EnrollmentForm(forms.ModelForm):
    # Дополнительные поля для продажи
    installment_parts = forms.IntegerField(
        label='Количество платежей при рассрочке',
        required=False,
        min_value=2,
        max_value=12,
        help_text='Оставьте пустым для единовременной оплаты'
    )
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.all(),
        label='Способ оплаты',
        required=False,
        help_text='Выберите способ оплаты (для рассрочки)'
    )

    class Meta:
        model = Enrollment
        fields = [
            'client',
            'product',
            'price',
            'lessons_total',
            'practices_total',
            'unlimited_practice',
            'installment_parts',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lessons_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'practices_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'unlimited_practice': forms.CheckboxInput(),
            'installment_parts': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Предзаполнение лимитов из продукта при создании
        if self.instance and self.instance.pk is None and 'product' in self.data:
            try:
                product_id = int(self.data.get('product'))
                product = Product.objects.get(id=product_id)
                self.fields['lessons_total'].initial = product.base_lessons
                self.fields['practices_total'].initial = product.base_practices
                self.fields['price'].initial = product.default_price
            except (ValueError, Product.DoesNotExist):
                pass
