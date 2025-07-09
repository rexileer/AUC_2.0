from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid

User = get_user_model()


class NotificationTemplate(models.Model):
    """Templates for different types of notifications"""

    NOTIFICATION_TYPES = [
        ('bid_placed', 'Bid Placed'),
        ('bid_outbid', 'Bid Outbid'),
        ('auction_ending', 'Auction Ending Soon'),
        ('auction_ended', 'Auction Ended'),
        ('auction_won', 'Auction Won'),
        ('auction_lost', 'Auction Lost'),
        ('new_item', 'New Item in Category'),
        ('price_drop', 'Price Drop'),
        ('comment_reply', 'Comment Reply'),
        ('payment_due', 'Payment Due'),
        ('welcome', 'Welcome Message'),
        ('custom', 'Custom Message'),
    ]

    DELIVERY_METHODS = [
        ('web', 'Web Notification'),
        ('email', 'Email'),
        ('telegram', 'Telegram'),
        ('all', 'All Methods'),
    ]

    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS)

    # Template content
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    html_template = models.TextField(blank=True)

    # Email specific
    subject_template = models.CharField(max_length=200, blank=True)

    # Telegram specific
    telegram_template = models.TextField(blank=True)

    # Web specific
    icon = models.CharField(max_length=50, blank=True)
    action_url = models.CharField(max_length=500, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_templates'
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        unique_together = ['notification_type', 'delivery_method']

    def __str__(self):
        return f"{self.name} ({self.delivery_method})"


class Notification(models.Model):
    """Base notification model"""

    NOTIFICATION_TYPES = [
        ('bid_placed', 'Bid Placed'),
        ('bid_outbid', 'Bid Outbid'),
        ('auction_ending', 'Auction Ending Soon'),
        ('auction_ended', 'Auction Ended'),
        ('auction_won', 'Auction Won'),
        ('auction_lost', 'Auction Lost'),
        ('new_item', 'New Item in Category'),
        ('price_drop', 'Price Drop'),
        ('comment_reply', 'Comment Reply'),
        ('payment_due', 'Payment Due'),
        ('welcome', 'Welcome Message'),
        ('system', 'System Notification'),
        ('custom', 'Custom Message'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')

    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Related object (auction item, bid, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Delivery tracking
    is_web_sent = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    is_telegram_sent = models.BooleanField(default=False)

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    data = models.JSONField(default=dict, blank=True)
    action_url = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} to {self.recipient.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def get_delivery_status(self):
        """Get delivery status summary"""
        return {
            'web': self.is_web_sent,
            'email': self.is_email_sent,
            'telegram': self.is_telegram_sent,
        }


class WebNotification(models.Model):
    """Web-specific notifications for real-time display"""

    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name='web_notification'
    )

    # Display settings
    icon = models.CharField(max_length=50, default='info')
    color = models.CharField(max_length=20, default='primary')
    show_toast = models.BooleanField(default=True)
    auto_dismiss = models.BooleanField(default=True)
    dismiss_timeout = models.PositiveIntegerField(default=5000)  # milliseconds

    # Interaction
    is_displayed = models.BooleanField(default=False)
    displayed_at = models.DateTimeField(null=True, blank=True)
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'web_notifications'
        verbose_name = 'Web Notification'
        verbose_name_plural = 'Web Notifications'

    def __str__(self):
        return f"Web: {self.notification.title}"

    def mark_displayed(self):
        """Mark as displayed"""
        if not self.is_displayed:
            self.is_displayed = True
            self.displayed_at = timezone.now()
            self.save(update_fields=['is_displayed', 'displayed_at'])

    def dismiss(self):
        """Dismiss notification"""
        if not self.is_dismissed:
            self.is_dismissed = True
            self.dismissed_at = timezone.now()
            self.notification.mark_as_read()
            self.save(update_fields=['is_dismissed', 'dismissed_at'])


class EmailNotification(models.Model):
    """Email-specific notifications"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]

    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name='email_notification'
    )

    # Email content
    subject = models.CharField(max_length=200)
    html_content = models.TextField(blank=True)
    text_content = models.TextField(blank=True)

    # Delivery
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)

    # Tracking
    email_id = models.CharField(max_length=100, blank=True)  # External email service ID
    bounce_reason = models.TextField(blank=True)

    # Retry logic
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'email_notifications'
        verbose_name = 'Email Notification'
        verbose_name_plural = 'Email Notifications'

    def __str__(self):
        return f"Email: {self.subject}"

    def mark_sent(self):
        """Mark email as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.notification.is_email_sent = True
        self.notification.save(update_fields=['is_email_sent'])
        self.save(update_fields=['status', 'sent_at'])

    def mark_failed(self, reason=""):
        """Mark email as failed"""
        self.status = 'failed'
        self.bounce_reason = reason
        self.retry_count += 1

        if self.retry_count < self.max_retries:
            # Schedule retry
            self.next_retry_at = timezone.now() + timezone.timedelta(minutes=5 * self.retry_count)
            self.status = 'pending'

        self.save(update_fields=['status', 'bounce_reason', 'retry_count', 'next_retry_at'])


class TelegramNotification(models.Model):
    """Telegram-specific notifications"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked by User'),
    ]

    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name='telegram_notification'
    )

    # Telegram content
    message_text = models.TextField()
    parse_mode = models.CharField(
        max_length=20,
        choices=[('HTML', 'HTML'), ('Markdown', 'Markdown')],
        default='HTML'
    )

    # Inline keyboard
    inline_keyboard = models.JSONField(null=True, blank=True)

    # Delivery
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)

    # Telegram API response
    message_id = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)

    # Retry logic
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'telegram_notifications'
        verbose_name = 'Telegram Notification'
        verbose_name_plural = 'Telegram Notifications'

    def __str__(self):
        return f"Telegram: {self.notification.title}"

    def mark_sent(self, message_id=""):
        """Mark telegram message as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.message_id = message_id
        self.notification.is_telegram_sent = True
        self.notification.save(update_fields=['is_telegram_sent'])
        self.save(update_fields=['status', 'sent_at', 'message_id'])

    def mark_failed(self, error_message=""):
        """Mark telegram message as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1

        if self.retry_count < self.max_retries and 'blocked' not in error_message.lower():
            # Schedule retry
            self.next_retry_at = timezone.now() + timezone.timedelta(minutes=5 * self.retry_count)
            self.status = 'pending'
        elif 'blocked' in error_message.lower():
            self.status = 'blocked'

        self.save(update_fields=['status', 'error_message', 'retry_count', 'next_retry_at'])


class NotificationPreference(models.Model):
    """User notification preferences"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')

    # Global settings
    enabled = models.BooleanField(default=True)

    # Delivery method preferences
    web_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    telegram_notifications = models.BooleanField(default=False)

    # Notification type preferences
    bid_notifications = models.BooleanField(default=True)
    auction_end_notifications = models.BooleanField(default=True)
    outbid_notifications = models.BooleanField(default=True)
    win_notifications = models.BooleanField(default=True)
    comment_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    marketing_notifications = models.BooleanField(default=False)

    # Timing preferences
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Frequency settings
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='never'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f"{self.user.username}'s Preferences"

    def should_send_notification(self, notification_type, delivery_method):
        """Check if notification should be sent based on preferences"""
        if not self.enabled:
            return False

        # Check delivery method
        if delivery_method == 'web' and not self.web_notifications:
            return False
        elif delivery_method == 'email' and not self.email_notifications:
            return False
        elif delivery_method == 'telegram' and not self.telegram_notifications:
            return False

        # Check notification type
        type_mapping = {
            'bid_placed': self.bid_notifications,
            'bid_outbid': self.outbid_notifications,
            'auction_ending': self.auction_end_notifications,
            'auction_ended': self.auction_end_notifications,
            'auction_won': self.win_notifications,
            'auction_lost': self.auction_end_notifications,
            'comment_reply': self.comment_notifications,
            'system': self.system_notifications,
            'custom': self.marketing_notifications,
        }

        return type_mapping.get(notification_type, True)

    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        now = timezone.now().time()
        return self.quiet_hours_start <= now <= self.quiet_hours_end


class BulkNotification(models.Model):
    """Bulk notifications sent by administrators"""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    TARGET_CHOICES = [
        ('all', 'All Users'),
        ('active', 'Active Users'),
        ('bidders', 'Users with Bids'),
        ('sellers', 'Users with Items'),
        ('winners', 'Users with Wins'),
        ('custom', 'Custom Query'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()

    # Targeting
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    target_users = models.ManyToManyField(User, blank=True)
    custom_query = models.TextField(blank=True)

    # Delivery settings
    send_web = models.BooleanField(default=True)
    send_email = models.BooleanField(default=False)
    send_telegram = models.BooleanField(default=False)

    # Email content
    email_subject = models.CharField(max_length=200, blank=True)
    email_html = models.TextField(blank=True)

    # Telegram content
    telegram_message = models.TextField(blank=True)

    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Statistics
    total_recipients = models.PositiveIntegerField(default=0)
    web_sent = models.PositiveIntegerField(default=0)
    email_sent = models.PositiveIntegerField(default=0)
    telegram_sent = models.PositiveIntegerField(default=0)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bulk_notifications_created')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bulk_notifications'
        verbose_name = 'Bulk Notification'
        verbose_name_plural = 'Bulk Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Bulk: {self.title}"

    def get_target_users(self):
        """Get users based on target type"""
        if self.target_type == 'all':
            return User.objects.filter(is_active=True)
        elif self.target_type == 'active':
            return User.objects.filter(is_active=True, last_login__gte=timezone.now() - timezone.timedelta(days=30))
        elif self.target_type == 'bidders':
            return User.objects.filter(bids__isnull=False).distinct()
        elif self.target_type == 'sellers':
            return User.objects.filter(selling_items__isnull=False).distinct()
        elif self.target_type == 'winners':
            return User.objects.filter(won_items__isnull=False).distinct()
        elif self.target_type == 'custom':
            return self.target_users.all()

        return User.objects.none()

    def send_notification(self):
        """Send bulk notification"""
        if self.status != 'draft':
            return

        self.status = 'sending'
        self.save()

        # Import here to avoid circular import
        from .tasks import send_bulk_notification_task
        send_bulk_notification_task.delay(self.id)


class NotificationLog(models.Model):
    """Log of all notification activities"""

    ACTION_CHOICES = [
        ('created', 'Created'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read'),
        ('dismissed', 'Dismissed'),
        ('expired', 'Expired'),
    ]

    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notification_logs'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification.title} - {self.action}"
