# celery_service.py
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Create the Celery app and configure it with Redis as the broker
celery_app = Celery(
    "paperbrain",
    broker=f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}",
    backend=f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}",
)

celery_app.conf.result_expires = 600  # Example: expires after 10 mins
celery_app.conf.task_max_retries = 5 # Retries and error handling
celery_app.conf.task_default_retry_delay = 60  # 1 minute

# importing here to avoid circular import
import app.task.podcast_task
import app.task.digest_task