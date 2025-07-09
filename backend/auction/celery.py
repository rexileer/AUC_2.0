import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auction.settings')

app = Celery('auction')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=60,  # 1 minute
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    result_expires=3600,  # 1 hour
    task_routes={
        'apps.auctions.tasks.process_bid': {'queue': 'auction_bids'},
        'apps.auctions.tasks.check_auction_endings': {'queue': 'auction_management'},
        'apps.auctions.tasks.send_auction_reminders': {'queue': 'notifications'},
        'apps.notifications.tasks.send_notification': {'queue': 'notifications'},
        'apps.notifications.tasks.send_bulk_notification': {'queue': 'notifications'},
        'apps.accounts.tasks.send_welcome_email': {'queue': 'emails'},
        'apps.accounts.tasks.send_verification_email': {'queue': 'emails'},
    },
)

# Optional configuration, see the application user guide.
app.conf.beat_schedule = {
    'check-auction-endings': {
        'task': 'apps.auctions.tasks.check_auction_endings',
        'schedule': 60.0,  # Run every minute
    },
    'send-auction-reminders': {
        'task': 'apps.auctions.tasks.send_auction_reminders',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'cleanup-expired-notifications': {
        'task': 'apps.notifications.tasks.cleanup_expired_notifications',
        'schedule': 3600.0,  # Run every hour
    },
    'update-auction-stats': {
        'task': 'apps.auctions.tasks.update_auction_statistics',
        'schedule': 1800.0,  # Run every 30 minutes
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
