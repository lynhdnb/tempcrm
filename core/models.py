from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class Client(models.Model):
    """Модель клиента (ученика)"""
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]

    first_name = models.CharField("Имя", max_length=50)
    last_name = models.CharField("Фамилия", max_length=50)
    middle_name = models.CharField("Отчество", max_length=50, blank=True)
    gender = models.CharField("Пол", max_length=1, choices=GENDER_CHOICES, blank=True)
    birth_date = models.DateField("Дата рождения", null=True, blank=True)

    phone = models.CharField("Телефон", max_length=20)
    email = models.EmailField("Email", blank=True)
    address = models.TextField("Адрес", blank=True)

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name="Родитель")

    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

class ContactPerson(models.Model):
    """Дополнительные контакты для клиента (например, второй родитель)"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='additional_contacts', verbose_name="Клиент")
    name = models.CharField("ФИО контакта", max_length=100)
    phone = models.CharField("Телефон", max_length=20)
    relation = models.CharField("Кем приходится", max_length=50, blank=True, help_text="Например: Мама, Папа")
    is_primary = models.BooleanField("Основной контакт", default=False)

    class Meta:
        verbose_name = "Контактное лицо"
        verbose_name_plural = "Контактные лица"

    def __str__(self):
        return f"{self.name} ({self.client})"

class EmployeeProfile(models.Model):
    """Расширенный профиль сотрудника (преподавателя/менеджера)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    phone = models.CharField("Рабочий телефон", max_length=20, blank=True)
    bio = models.TextField("О себе", blank=True)
    hire_date = models.DateField("Дата приема", null=True, blank=True)

    instruments = models.CharField("Инструменты", max_length=200, blank=True, help_text="Через запятую: Фортепиано, Гитара")
    hourly_rate = models.DecimalField("Ставка за час", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Профиль сотрудника"
        verbose_name_plural = "Профили сотрудников"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"