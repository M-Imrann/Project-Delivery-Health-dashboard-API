import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Health_Dashboard.settings")

app = Celery("Health_Dashboard")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
