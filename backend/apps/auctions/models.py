from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.utils.text import slugify
from decimal import Decimal
import uuid
from datetime import timedelta

User = get_user_model()


class Category(models.Model):
    """Auction item categories"""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='children'
    )

    # Display settings
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auction_categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('auctions:category', kwargs={'slug': self.slug})

    def get_full_path(self):
        """Get full category path"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name


class AuctionItem(models.Model):
    """Main auction item model"""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
        ('sold', 'Sold'),
    ]

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')

    # Seller Information
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='selling_items')

    # Auction Settings
    starting_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    reserve_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    buy_now_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    min_bid_increment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    # Timing
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()
    auto_extend_time = models.PositiveIntegerField(default=300)  # seconds

    # Current Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    current_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_bids = models.PositiveIntegerField(default=0)

    # Winner Information
    winner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_items'
    )
    winning_bid = models.OneToOneField(
        'Bid',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='winning_item'
    )

    # Additional Information
    location = models.CharField(max_length=200, blank=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True)

    # Settings
    allow_questions = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_sponsored = models.BooleanField(default=False)

    # Statistics
    view_count = models.PositiveIntegerField(default=0)
    watch_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auction_items'
        verbose_name = 'Auction Item'
        verbose_name_plural = 'Auction Items'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Set current price to starting price if no bids
        if self.total_bids == 0:
            self.current_price = self.starting_price

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('auctions:item_detail', kwargs={'slug': self.slug})

    def is_active(self):
        """Check if auction is currently active"""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_time <= now <= self.end_time
        )

    def is_ended(self):
        """Check if auction has ended"""
        return timezone.now() > self.end_time or self.status == 'ended'

    def time_left(self):
        """Get time left in auction"""
        if self.is_ended():
            return timedelta(0)
        return self.end_time - timezone.now()

    def get_next_bid_amount(self):
        """Get minimum next bid amount"""
        return self.current_price + self.min_bid_increment

    def can_bid(self, user, amount):
        """Check if user can place a bid"""
        if not self.is_active():
            return False, "Auction is not active"

        if user == self.seller:
            return False, "You cannot bid on your own item"

        if amount < self.get_next_bid_amount():
            return False, f"Bid must be at least {self.get_next_bid_amount()}"

        if not user.can_bid(amount):
            return False, "Insufficient balance"

        return True, "Valid bid"

    def place_bid(self, user, amount):
        """Place a bid on this item"""
        can_bid, message = self.can_bid(user, amount)

        if not can_bid:
            raise ValueError(message)

        # Check if auction should be extended
        time_left = self.time_left()
        if time_left.total_seconds() < self.auto_extend_time:
            self.end_time = timezone.now() + timedelta(seconds=self.auto_extend_time)
            self.save()

        # Create bid
        bid = Bid.objects.create(
            item=self,
            bidder=user,
            amount=amount
        )

        # Update item
        self.current_price = amount
        self.total_bids += 1
        self.save()

        return bid

    def get_highest_bid(self):
        """Get the highest bid"""
        return self.bids.order_by('-amount').first()

    def get_watchers(self):
        """Get users watching this item"""
        return User.objects.filter(watching_items__item=self)

    def has_reserve_met(self):
        """Check if reserve price has been met"""
        if not self.reserve_price:
            return True
        return self.current_price >= self.reserve_price

    def end_auction(self):
        """End the auction and determine winner"""
        if self.status != 'active':
            return

        self.status = 'ended'

        highest_bid = self.get_highest_bid()
        if highest_bid and self.has_reserve_met():
            self.winner = highest_bid.bidder
            self.winning_bid = highest_bid
            self.status = 'sold'

        self.save()

    def get_main_image(self):
        """Get main image for the item"""
        return self.images.filter(is_main=True).first()

    def get_images(self):
        """Get all images for the item"""
        return self.images.all().order_by('order')


class AuctionImage(models.Model):
    """Images for auction items"""

    item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='auction_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auction_images'
        verbose_name = 'Auction Image'
        verbose_name_plural = 'Auction Images'
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.item.title}"

    def save(self, *args, **kwargs):
        # Ensure only one main image per item
        if self.is_main:
            AuctionImage.objects.filter(item=self.item, is_main=True).update(is_main=False)
        super().save(*args, **kwargs)


class Bid(models.Model):
    """Bids on auction items"""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('outbid', 'Outbid'),
        ('winning', 'Winning'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]

    item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Automatic bidding
    max_bid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auction_bids'
        verbose_name = 'Bid'
        verbose_name_plural = 'Bids'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bidder.username} - {self.amount} on {self.item.title}"

    def save(self, *args, **kwargs):
        # Mark previous bids as outbid
        if self.pk is None:  # New bid
            self.item.bids.exclude(bidder=self.bidder).update(status='outbid')

        super().save(*args, **kwargs)


class Comment(models.Model):
    """Comments on auction items"""

    item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='replies'
    )

    comment = models.TextField()
    is_question = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auction_comments'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.item.title}"

    def get_replies(self):
        """Get all replies to this comment"""
        return self.replies.all()


class WatchList(models.Model):
    """Users watching auction items"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watching_items')
    item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='watchers')

    # Notification preferences for this item
    notify_on_bid = models.BooleanField(default=True)
    notify_on_price_change = models.BooleanField(default=True)
    notify_on_ending_soon = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auction_watchlist'
        verbose_name = 'Watch List'
        verbose_name_plural = 'Watch Lists'
        unique_together = ['user', 'item']

    def __str__(self):
        return f"{self.user.username} watching {self.item.title}"


class AuctionHistory(models.Model):
    """History of auction activities"""

    ACTION_CHOICES = [
        ('created', 'Auction Created'),
        ('bid_placed', 'Bid Placed'),
        ('bid_outbid', 'Bid Outbid'),
        ('extended', 'Auction Extended'),
        ('ended', 'Auction Ended'),
        ('sold', 'Item Sold'),
        ('cancelled', 'Auction Cancelled'),
        ('comment_added', 'Comment Added'),
        ('watched', 'Item Watched'),
        ('unwatched', 'Item Unwatched'),
    ]

    item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auction_history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auction_history'
        verbose_name = 'Auction History'
        verbose_name_plural = 'Auction History'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.item.title}"


class SavedSearch(models.Model):
    """Saved searches for users"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    query = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    condition = models.CharField(max_length=20, choices=AuctionItem.CONDITION_CHOICES, blank=True)

    # Notification settings
    notify_on_match = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auction_saved_searches'
        verbose_name = 'Saved Search'
        verbose_name_plural = 'Saved Searches'

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    def get_matching_items(self):
        """Get items matching this saved search"""
        queryset = AuctionItem.objects.filter(status='active')

        if self.query:
            queryset = queryset.filter(title__icontains=self.query)

        if self.category:
            queryset = queryset.filter(category=self.category)

        if self.min_price:
            queryset = queryset.filter(current_price__gte=self.min_price)

        if self.max_price:
            queryset = queryset.filter(current_price__lte=self.max_price)

        if self.condition:
            queryset = queryset.filter(condition=self.condition)

        return queryset


class AuctionReport(models.Model):
    """Reports for auction items"""

    REPORT_TYPES = [
        ('inappropriate', 'Inappropriate Content'),
        ('spam', 'Spam'),
        ('fraud', 'Fraudulent Activity'),
        ('copyright', 'Copyright Infringement'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_reviewed'
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auction_reports'
        verbose_name = 'Auction Report'
        verbose_name_plural = 'Auction Reports'
        unique_together = ['item', 'reporter']

    def __str__(self):
        return f"Report by {self.reporter.username} for {self.item.title}"
