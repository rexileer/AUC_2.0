from django.apps import AppConfig


class BotIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bot_integration'
    verbose_name = 'Bot Integration'

    def ready(self):
        # Import signal handlers
        try:
            import apps.bot_integration.signals
        except ImportError:
            pass
