import os
import sys

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, '/home/c17919/muserp.na4u.ru')

# Указываем Django, где файл настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'music_school_erp.settings')

# Загружаем WSGI-приложение
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()