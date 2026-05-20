import os
from celery import Celery

os.environ.setdefault('config.settings')

app=Celery('url_health')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()