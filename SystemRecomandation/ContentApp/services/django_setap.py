import os
import sys
import django


def configure_django():
    """Функция для настройки Django в сторонних скриптах"""
    project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(project_path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SystemRecomandation.settings')

    django.setup()

    return True