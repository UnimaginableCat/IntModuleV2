import os
from celery import Celery

from IntModuleV2 import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IntModuleV2.settings')

app = Celery('IntModuleV2')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


