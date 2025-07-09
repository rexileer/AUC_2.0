from django.apps import AppConfig


class AuctionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auctions'
    verbose_name = 'Auction Management'

    def ready(self):
        # Import signal handlers
        try:
            import apps.auctions.signals
        except ImportError:
            pass
