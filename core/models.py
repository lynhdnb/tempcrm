from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Владелец'),
        ('admin', 'Админ'),
        ('manager', 'Менеджер'),
        ('teacher', 'Преподаватель'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='manager')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')

    def __str__(self):
        full_name = f"{self.user.last_name} {self.user.first_name}".strip()
        if not full_name:
            full_name = self.user.username
        return f"{full_name} ({self.get_role_display()})"
