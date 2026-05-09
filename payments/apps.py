from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = 'Платежи'

    def ready(self):
        # Импортируем сигналы при запуске
        from . import signals
