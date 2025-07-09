from django.urls import re_path, path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from . import consumers

# WebSocket URL patterns for notifications
websocket_urlpatterns = [
    # User-specific notification stream
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/notifications/(?P<user_id>\d+)/$', consumers.UserNotificationConsumer.as_asgi()),

    # Admin notification broadcasting
    re_path(r'ws/admin/notifications/$', consumers.AdminNotificationConsumer.as_asgi()),

    # Auction-specific notifications
    re_path(r'ws/auction/(?P<auction_id>\d+)/$', consumers.AuctionNotificationConsumer.as_asgi()),

    # Global notification feed
    re_path(r'ws/feed/$', consumers.NotificationFeedConsumer.as_asgi()),
]
