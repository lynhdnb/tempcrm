from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Основные данные'

    def ready(self):
        # Импортируем сигналы при запуске
        from . import signals
