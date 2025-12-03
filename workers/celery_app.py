# workers/celery_app.py
"""
Celery Application Configuration

Sets up the Celery app for background job processing.

Usage:
    # Start worker
    celery -A workers.celery_app worker --loglevel=info
    
    # Start with concurrency
    celery -A workers.celery_app worker --loglevel=info --concurrency=4
    
    # Monitor with Flower
    celery -A workers.celery_app flower
"""

import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration - use REDIS_URL for Upstash, fallback to localhost for dev
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Create Celery app
app = Celery(
    "skyt_workers",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["workers.tasks"],
)

# Celery configuration
app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,  # Acknowledge after task completes (reliability)
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    task_time_limit=600,  # 10 minute hard limit
    task_soft_time_limit=540,  # 9 minute soft limit (allows cleanup)
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Fetch one task at a time (fairness)
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (memory)
    
    # Result backend
    result_expires=86400,  # Results expire after 24 hours
    
    # Rate limiting
    task_default_rate_limit="10/m",  # 10 tasks per minute default
    
    # Retry settings
    task_default_retry_delay=5,  # 5 seconds between retries
    task_max_retries=3,
    
    # Queue routing
    task_routes={
        "workers.tasks.execute_skyt_job": {"queue": "skyt_jobs"},
        "workers.tasks.execute_skyt_job_high_priority": {"queue": "skyt_priority"},
    },
    
    # Beat scheduler (for periodic tasks)
    beat_schedule={
        "cleanup-old-jobs": {
            "task": "workers.tasks.cleanup_old_jobs",
            "schedule": 3600.0,  # Every hour
        },
    },
)


if __name__ == "__main__":
    app.start()
