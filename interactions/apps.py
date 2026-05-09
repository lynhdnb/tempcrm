from django.apps import AppConfig


class InteractionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interactions'
    verbose_name = 'Взаимодействия'

    def ready(self):
        # Импортируем сигналы при запуске
        from . import signals
