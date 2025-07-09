from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()


class BotUser(models.Model):
    """Telegram bot user integration"""

    REGISTRATION_STATUS = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('blocked', 'Blocked'),
    ]

    # Telegram user info
    telegram_id = models.CharField(max_length=20, unique=True)
    telegram_username = models.CharField(max_length=50, blank=True, null=True)
    telegram_first_name = models.CharField(max_length=50, blank=True)
    telegram_last_name = models.CharField(max_length=50, blank=True)
    telegram_language_code = models.CharField(max_length=10, blank=True)

    # Django user link
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='bot_user',
        null=True,
        blank=True
    )

    # Registration status
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='pending')
    api_key_linked = models.BooleanField(default=False)

    # Bot preferences
    notifications_enabled = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en')

    # Usage statistics
    total_commands = models.PositiveIntegerField(default=0)
    last_command_at = models.DateTimeField(null=True, blank=True)

    # Registration data
    registration_code = models.CharField(max_length=10, blank=True)
    registration_expires = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bot_users'
        verbose_name = 'Bot User'
        verbose_name_plural = 'Bot Users'
        ordering = ['-created_at']

    def __str__(self):
        display_name = self.telegram_username or f"{self.telegram_first_name} {self.telegram_last_name}".strip()
        return f"Bot User: {display_name} ({self.telegram_id})"

    def get_display_name(self):
        """Get display name for bot user"""
        if self.telegram_username:
            return f"@{self.telegram_username}"
        return f"{self.telegram_first_name} {self.telegram_last_name}".strip()

    def is_linked(self):
        """Check if bot user is linked to a Django user"""
        return self.user is not None and self.api_key_linked

    def link_user(self, user):
        """Link bot user to Django user"""
        self.user = user
        self.api_key_linked = True
        self.status = 'active'
        self.save()

    def unlink_user(self):
        """Unlink bot user from Django user"""
        self.user = None
        self.api_key_linked = False
        self.status = 'pending'
        self.save()

    def increment_command_count(self):
        """Increment command count and update last command time"""
        self.total_commands += 1
        self.last_command_at = timezone.now()
        self.save(update_fields=['total_commands', 'last_command_at'])


class BotCommand(models.Model):
    """Bot command history and analytics"""

    COMMAND_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot_user = models.ForeignKey(BotUser, on_delete=models.CASCADE, related_name='commands')

    # Command details
    command = models.CharField(max_length=100)
    command_args = models.JSONField(default=dict, blank=True)
    raw_message = models.TextField(blank=True)

    # Response details
    response_message = models.TextField(blank=True)
    response_data = models.JSONField(default=dict, blank=True)

    # Status and timing
    status = models.CharField(max_length=20, choices=COMMAND_STATUS, default='pending')
    processing_time = models.DurationField(null=True, blank=True)

    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)

    # Metadata
    session_id = models.CharField(max_length=100, blank=True)
    message_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bot_commands'
        verbose_name = 'Bot Command'
        verbose_name_plural = 'Bot Commands'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bot_user', 'command']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.bot_user.get_display_name()} - {self.command}"

    def mark_completed(self, response_message="", response_data=None):
        """Mark command as completed"""
        self.status = 'completed'
        self.response_message = response_message
        self.response_data = response_data or {}
        self.completed_at = timezone.now()

        if self.created_at:
            self.processing_time = self.completed_at - self.created_at

        self.save()

    def mark_failed(self, error_message=""):
        """Mark command as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()

        if self.created_at:
            self.processing_time = self.completed_at - self.created_at

        self.save()


class BotSession(models.Model):
    """Bot conversation sessions"""

    SESSION_STATUS = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot_user = models.ForeignKey(BotUser, on_delete=models.CASCADE, related_name='sessions')

    # Session details
    session_type = models.CharField(max_length=50)  # e.g., 'api_key_input', 'item_search', etc.
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='active')

    # Session data
    context_data = models.JSONField(default=dict, blank=True)
    current_step = models.CharField(max_length=50, blank=True)

    # Timing
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bot_sessions'
        verbose_name = 'Bot Session'
        verbose_name_plural = 'Bot Sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bot_user.get_display_name()} - {self.session_type}"

    def is_active(self):
        """Check if session is still active"""
        return self.status == 'active' and timezone.now() < self.expires_at

    def update_context(self, key, value):
        """Update session context data"""
        self.context_data[key] = value
        self.save(update_fields=['context_data', 'updated_at'])

    def get_context(self, key, default=None):
        """Get value from session context"""
        return self.context_data.get(key, default)

    def complete_session(self):
        """Mark session as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def cancel_session(self):
        """Cancel the session"""
        self.status = 'cancelled'
        self.completed_at = timezone.now()
        self.save()


class BotNotificationSettings(models.Model):
    """Bot-specific notification settings"""

    bot_user = models.OneToOneField(
        BotUser,
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )

    # General settings
    enabled = models.BooleanField(default=True)

    # Notification types
    bid_notifications = models.BooleanField(default=True)
    outbid_notifications = models.BooleanField(default=True)
    auction_end_notifications = models.BooleanField(default=True)
    win_notifications = models.BooleanField(default=True)
    new_item_notifications = models.BooleanField(default=False)
    price_drop_notifications = models.BooleanField(default=False)

    # Timing settings
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    # Frequency settings
    max_notifications_per_hour = models.PositiveIntegerField(default=10)
    digest_mode = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bot_notification_settings'
        verbose_name = 'Bot Notification Settings'
        verbose_name_plural = 'Bot Notification Settings'

    def __str__(self):
        return f"Notification Settings for {self.bot_user.get_display_name()}"

    def should_send_notification(self, notification_type):
        """Check if notification should be sent based on settings"""
        if not self.enabled:
            return False

        # Check notification type
        type_mapping = {
            'bid_placed': self.bid_notifications,
            'bid_outbid': self.outbid_notifications,
            'auction_ending': self.auction_end_notifications,
            'auction_ended': self.auction_end_notifications,
            'auction_won': self.win_notifications,
            'new_item': self.new_item_notifications,
            'price_drop': self.price_drop_notifications,
        }

        return type_mapping.get(notification_type, True)

    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        now = timezone.now().time()
        return self.quiet_hours_start <= now <= self.quiet_hours_end


class BotAnalytics(models.Model):
    """Bot usage analytics"""

    date = models.DateField()

    # User metrics
    total_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)

    # Command metrics
    total_commands = models.PositiveIntegerField(default=0)
    unique_commands = models.PositiveIntegerField(default=0)
    failed_commands = models.PositiveIntegerField(default=0)

    # Popular commands
    command_stats = models.JSONField(default=dict, blank=True)

    # Response times
    avg_response_time = models.DurationField(null=True, blank=True)

    # Notification metrics
    notifications_sent = models.PositiveIntegerField(default=0)
    notifications_failed = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bot_analytics'
        verbose_name = 'Bot Analytics'
        verbose_name_plural = 'Bot Analytics'
        unique_together = ['date']
        ordering = ['-date']

    def __str__(self):
        return f"Bot Analytics for {self.date}"


class BotWebhook(models.Model):
    """Bot webhook event log"""

    EVENT_TYPES = [
        ('message', 'Message'),
        ('callback_query', 'Callback Query'),
        ('inline_query', 'Inline Query'),
        ('pre_checkout_query', 'Pre Checkout Query'),
        ('shipping_query', 'Shipping Query'),
        ('poll_answer', 'Poll Answer'),
        ('my_chat_member', 'My Chat Member'),
        ('chat_member', 'Chat Member'),
        ('chat_join_request', 'Chat Join Request'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Event details
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    telegram_update_id = models.CharField(max_length=100)

    # User info
    telegram_user_id = models.CharField(max_length=20, blank=True)
    telegram_username = models.CharField(max_length=50, blank=True)

    # Raw data
    raw_data = models.JSONField()

    # Processing info
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bot_webhooks'
        verbose_name = 'Bot Webhook'
        verbose_name_plural = 'Bot Webhooks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['telegram_update_id']),
            models.Index(fields=['telegram_user_id']),
            models.Index(fields=['processed']),
        ]

    def __str__(self):
        return f"Webhook: {self.event_type} - {self.telegram_update_id}"

    def mark_processed(self):
        """Mark webhook as processed"""
        self.processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=['processed', 'processed_at'])

    def mark_error(self, error_message):
        """Mark webhook processing error"""
        self.processing_error = error_message
        self.processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=['processing_error', 'processed', 'processed_at'])


class BotConfiguration(models.Model):
    """Bot configuration settings"""

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)

    # Value type for proper parsing
    value_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
        ],
        default='string'
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bot_configuration'
        verbose_name = 'Bot Configuration'
        verbose_name_plural = 'Bot Configurations'
        ordering = ['key']

    def __str__(self):
        return f"Bot Config: {self.key}"

    def get_value(self):
        """Get parsed value based on type"""
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == 'json':
            return json.loads(self.value)

        return self.value

    def set_value(self, value):
        """Set value with proper type conversion"""
        if self.value_type == 'json':
            self.value = json.dumps(value)
        else:
            self.value = str(value)

        self.save()

    @classmethod
    def get_config(cls, key, default=None):
        """Get configuration value by key"""
        try:
            config = cls.objects.get(key=key, is_active=True)
            return config.get_value()
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_config(cls, key, value, description="", value_type="string"):
        """Set configuration value"""
        config, created = cls.objects.get_or_create(
            key=key,
            defaults={
                'value': str(value),
                'description': description,
                'value_type': value_type
            }
        )

        if not created:
            config.set_value(value)

        return config
