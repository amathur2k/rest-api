from celery import Celery
from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# Initialize Celery
celery = Celery(
    __name__,
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['tasks']  # List of modules to import tasks from
)

# Optional Celery configuration
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Add other configurations if needed
)

# Explicitly import tasks module after app is defined
# This can sometimes help with discovery issues.
import tasks
