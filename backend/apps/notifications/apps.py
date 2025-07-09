from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notification System'

    def ready(self):
        # Import signal handlers
        try:
            import apps.notifications.signals
        except ImportError:
            pass
