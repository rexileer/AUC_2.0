from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
import uuid
import secrets
import string


class User(AbstractUser):
    """Custom User model for auction platform"""

    # Basic Info
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)

    # Profile
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = PhoneNumberField(blank=True, null=True)

    # Address Information
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Auction-specific fields
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )

    # Bot Integration
    api_key = models.CharField(max_length=64, unique=True, blank=True)
    telegram_user_id = models.CharField(max_length=20, blank=True, null=True)
    telegram_username = models.CharField(max_length=50, blank=True, null=True)

    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    telegram_notifications = models.BooleanField(default=False)
    web_notifications = models.BooleanField(default=True)

    # Notification Types
    notify_on_bid = models.BooleanField(default=True)
    notify_on_outbid = models.BooleanField(default=True)
    notify_on_auction_end = models.BooleanField(default=True)
    notify_on_auction_win = models.BooleanField(default=True)
    notify_on_new_items = models.BooleanField(default=False)
    notify_on_price_drops = models.BooleanField(default=False)

    # Verification
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True)
    verification_code_expires = models.DateTimeField(blank=True, null=True)

    # Ratings
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    rating_count = models.PositiveIntegerField(default=0)

    # Account Status
    is_seller = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True)
    ban_expires = models.DateTimeField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the full name of the user"""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Return the short name for the user"""
        return self.first_name or self.username

    def save(self, *args, **kwargs):
        """Override save to generate API key if not exists"""
        if not self.api_key:
            self.api_key = self.generate_api_key()
        super().save(*args, **kwargs)

    def generate_api_key(self):
        """Generate a unique API key for bot integration"""
        while True:
            api_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
            if not User.objects.filter(api_key=api_key).exists():
                return api_key

    def regenerate_api_key(self):
        """Regenerate API key"""
        self.api_key = self.generate_api_key()
        self.save()
        return self.api_key

    def can_bid(self, amount):
        """Check if user can place a bid of given amount"""
        return self.balance >= amount and not self.is_banned

    def deduct_balance(self, amount):
        """Deduct amount from user balance"""
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False

    def add_balance(self, amount):
        """Add amount to user balance"""
        self.balance += amount
        self.save()

    def update_rating(self, new_rating):
        """Update user rating"""
        total_rating = (self.rating * self.rating_count) + new_rating
        self.rating_count += 1
        self.rating = total_rating / self.rating_count
        self.save()

    def get_display_name(self):
        """Get display name for user"""
        if self.get_full_name():
            return self.get_full_name()
        return self.username

    def has_complete_profile(self):
        """Check if user has completed their profile"""
        return all([
            self.first_name,
            self.last_name,
            self.phone_number,
            self.address_line1,
            self.city,
            self.postal_code,
            self.country
        ])

    def get_notification_preferences(self):
        """Get user notification preferences as dict"""
        return {
            'email': self.email_notifications,
            'telegram': self.telegram_notifications,
            'web': self.web_notifications,
            'on_bid': self.notify_on_bid,
            'on_outbid': self.notify_on_outbid,
            'on_auction_end': self.notify_on_auction_end,
            'on_auction_win': self.notify_on_auction_win,
            'on_new_items': self.notify_on_new_items,
            'on_price_drops': self.notify_on_price_drops,
        }


class UserProfile(models.Model):
    """Extended user profile information"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Social Media
    website = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    # Preferences
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    currency = models.CharField(max_length=3, default='USD')

    # Statistics
    total_bids = models.PositiveIntegerField(default=0)
    total_wins = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Seller Info
    seller_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    seller_rating_count = models.PositiveIntegerField(default=0)
    total_items_sold = models.PositiveIntegerField(default=0)

    # Privacy Settings
    show_email = models.BooleanField(default=False)
    show_phone = models.BooleanField(default=False)
    show_address = models.BooleanField(default=False)
    show_statistics = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_win_rate(self):
        """Calculate win rate percentage"""
        if self.total_bids == 0:
            return 0
        return (self.total_wins / self.total_bids) * 100

    def get_average_spent_per_win(self):
        """Calculate average amount spent per win"""
        if self.total_wins == 0:
            return 0
        return self.total_spent / self.total_wins


class UserTransaction(models.Model):
    """User balance transactions"""

    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdrawal'),
        ('bid', 'Bid Placed'),
        ('refund', 'Bid Refund'),
        ('payment', 'Payment'),
        ('bonus', 'Bonus'),
        ('penalty', 'Penalty'),
    ]

    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    description = models.TextField(blank=True)
    reference_id = models.CharField(max_length=100, blank=True)

    # Related objects
    auction_item = models.ForeignKey(
        'auctions.AuctionItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    bid = models.ForeignKey(
        'auctions.Bid',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_transactions'
        verbose_name = 'User Transaction'
        verbose_name_plural = 'User Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"


class UserVerification(models.Model):
    """User verification records"""

    VERIFICATION_TYPES = [
        ('email', 'Email Verification'),
        ('phone', 'Phone Verification'),
        ('identity', 'Identity Verification'),
        ('address', 'Address Verification'),
        ('payment', 'Payment Method Verification'),
    ]

    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifications')
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verification_code = models.CharField(max_length=10, blank=True)
    verification_data = models.JSONField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_verifications'
        verbose_name = 'User Verification'
        verbose_name_plural = 'User Verifications'
        unique_together = ['user', 'verification_type']

    def __str__(self):
        return f"{self.user.username} - {self.verification_type} - {self.status}"

    def is_expired(self):
        """Check if verification is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def mark_verified(self):
        """Mark verification as verified"""
        self.status = 'verified'
        self.verified_at = timezone.now()
        self.save()


class UserFeedback(models.Model):
    """User feedback and ratings"""

    FEEDBACK_TYPES = [
        ('buyer', 'Buyer Feedback'),
        ('seller', 'Seller Feedback'),
    ]

    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedback_given'
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedback_received'
    )
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)

    auction_item = models.ForeignKey(
        'auctions.AuctionItem',
        on_delete=models.CASCADE,
        related_name='feedback'
    )

    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_feedback'
        verbose_name = 'User Feedback'
        verbose_name_plural = 'User Feedback'
        unique_together = ['from_user', 'to_user', 'auction_item', 'feedback_type']

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.rating} stars)"
