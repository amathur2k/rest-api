import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

# Celery Config
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Upload Folder
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")
