import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """Basic notification consumer for authenticated users"""

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        self.user_group_name = f'user_{self.user.id}_notifications'

        # Join user notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"User {self.user.id} connected to notifications")

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to notifications'
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        logger.info(f"User disconnected from notifications: {close_code}")

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            if message_type == 'mark_read':
                await self.handle_mark_read(text_data_json)
            elif message_type == 'get_unread_count':
                await self.handle_get_unread_count()
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def handle_mark_read(self, data):
        """Mark notification as read"""
        notification_id = data.get('notification_id')
        if notification_id:
            # Here you would mark the notification as read in the database
            await self.send(text_data=json.dumps({
                'type': 'marked_read',
                'notification_id': notification_id
            }))

    async def handle_get_unread_count(self):
        """Get unread notification count"""
        # Here you would get the actual count from database
        count = 0  # Placeholder
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': count
        }))

    # Handle messages sent to the group
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))

    async def notification_update(self, event):
        """Send notification update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification_update',
            'update': event['update']
        }))


class UserNotificationConsumer(AsyncWebsocketConsumer):
    """User-specific notification consumer"""

    async def connect(self):
        """Handle WebSocket connection for specific user"""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = self.scope["user"]

        # Only allow users to connect to their own notifications or admins
        if (self.user.is_anonymous or
            (int(self.user_id) != self.user.id and not self.user.is_staff)):
            await self.close()
            return

        self.group_name = f'user_{self.user_id}_notifications'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"Connected to user {self.user_id} notifications")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'subscribe_to_auction':
                await self.handle_auction_subscription(data)
            elif message_type == 'unsubscribe_from_auction':
                await self.handle_auction_unsubscription(data)
        except json.JSONDecodeError:
            pass

    async def handle_auction_subscription(self, data):
        """Subscribe to auction notifications"""
        auction_id = data.get('auction_id')
        if auction_id:
            auction_group = f'auction_{auction_id}_notifications'
            await self.channel_layer.group_add(
                auction_group,
                self.channel_name
            )

    async def handle_auction_unsubscription(self, data):
        """Unsubscribe from auction notifications"""
        auction_id = data.get('auction_id')
        if auction_id:
            auction_group = f'auction_{auction_id}_notifications'
            await self.channel_layer.group_discard(
                auction_group,
                self.channel_name
            )

    # Handle messages sent to the group
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps(event))

    async def auction_update(self, event):
        """Send auction update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'auction_update',
            'update': event['update']
        }))


class AdminNotificationConsumer(AsyncWebsocketConsumer):
    """Admin notification broadcasting consumer"""

    async def connect(self):
        """Handle WebSocket connection for admin"""
        self.user = self.scope["user"]

        if self.user.is_anonymous or not self.user.is_staff:
            await self.close()
            return

        self.group_name = 'admin_notifications'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"Admin {self.user.id} connected to admin notifications")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'broadcast_notification':
                await self.handle_broadcast_notification(data)
        except json.JSONDecodeError:
            pass

    async def handle_broadcast_notification(self, data):
        """Handle broadcasting notification to all users"""
        # Here you would create and send bulk notifications
        await self.send(text_data=json.dumps({
            'type': 'broadcast_sent',
            'message': 'Notification broadcasted successfully'
        }))

    # Handle messages sent to the group
    async def admin_message(self, event):
        """Send admin message to WebSocket"""
        await self.send(text_data=json.dumps(event))


class AuctionNotificationConsumer(AsyncWebsocketConsumer):
    """Auction-specific notification consumer"""

    async def connect(self):
        """Handle WebSocket connection for auction"""
        self.auction_id = self.scope['url_route']['kwargs']['auction_id']
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f'auction_{self.auction_id}_notifications'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"User {self.user.id} connected to auction {self.auction_id} notifications")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'place_bid':
                await self.handle_place_bid(data)
            elif message_type == 'watch_auction':
                await self.handle_watch_auction()
        except json.JSONDecodeError:
            pass

    async def handle_place_bid(self, data):
        """Handle bid placement"""
        bid_amount = data.get('amount')
        # Here you would process the bid and notify other users
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'bid_placed',
                'bid': {
                    'amount': bid_amount,
                    'user': self.user.username,
                    'auction_id': self.auction_id
                }
            }
        )

    async def handle_watch_auction(self):
        """Handle watching auction"""
        # Here you would add user to watchers
        pass

    # Handle messages sent to the group
    async def bid_placed(self, event):
        """Send bid notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'bid_placed',
            'bid': event['bid']
        }))

    async def auction_ended(self, event):
        """Send auction end notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'auction_ended',
            'auction': event['auction']
        }))

    async def auction_extended(self, event):
        """Send auction extension notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'auction_extended',
            'extension': event['extension']
        }))


class NotificationFeedConsumer(AsyncWebsocketConsumer):
    """Global notification feed consumer"""

    async def connect(self):
        """Handle WebSocket connection for global feed"""
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = 'global_notification_feed'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"User {self.user.id} connected to global notification feed")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'get_recent_activity':
                await self.handle_get_recent_activity()
        except json.JSONDecodeError:
            pass

    async def handle_get_recent_activity(self):
        """Get recent auction activity"""
        # Here you would get recent activity from database
        await self.send(text_data=json.dumps({
            'type': 'recent_activity',
            'activities': []  # Placeholder
        }))

    # Handle messages sent to the group
    async def global_notification(self, event):
        """Send global notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'global_notification',
            'notification': event['notification']
        }))

    async def system_message(self, event):
        """Send system message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': event['message']
        }))
