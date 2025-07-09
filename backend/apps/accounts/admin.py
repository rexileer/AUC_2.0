from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from django.utils import timezone
from .models import User, UserProfile, UserTransaction, UserVerification, UserFeedback


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    extra = 0
    fieldsets = (
        ('Social Media', {
            'fields': ('website', 'facebook', 'twitter', 'instagram')
        }),
        ('Preferences', {
            'fields': ('timezone', 'language', 'currency')
        }),
        ('Statistics', {
            'fields': ('total_bids', 'total_wins', 'total_spent', 'total_earned'),
            'classes': ('collapse',)
        }),
        ('Seller Info', {
            'fields': ('seller_rating', 'seller_rating_count', 'total_items_sold'),
            'classes': ('collapse',)
        }),
        ('Privacy Settings', {
            'fields': ('show_email', 'show_phone', 'show_address', 'show_statistics'),
            'classes': ('collapse',)
        }),
    )


class UserTransactionInline(admin.TabularInline):
    model = UserTransaction
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('transaction_type', 'amount', 'status', 'description', 'created_at')
    can_delete = False


class UserVerificationInline(admin.TabularInline):
    model = UserVerification
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'verified_at')
    fields = ('verification_type', 'status', 'verification_code', 'expires_at', 'verified_at')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = (
        'email', 'username', 'get_full_name', 'balance', 'is_verified',
        'is_seller', 'rating', 'created_at', 'last_login', 'is_active'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'is_verified', 'is_seller',
        'is_banned', 'email_notifications', 'telegram_notifications',
        'created_at', 'last_login'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name', 'telegram_username')
    ordering = ('-created_at',)
    filter_horizontal = ()

    fieldsets = (
        ('Login Info', {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'avatar', 'bio', 'phone_number')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Account Settings', {
            'fields': ('balance', 'api_key', 'is_verified', 'is_seller', 'rating', 'rating_count')
        }),
        ('Telegram Integration', {
            'fields': ('telegram_user_id', 'telegram_username'),
            'classes': ('collapse',)
        }),
        ('Notification Preferences', {
            'fields': (
                'email_notifications', 'telegram_notifications', 'web_notifications',
                'notify_on_bid', 'notify_on_outbid', 'notify_on_auction_end',
                'notify_on_auction_win', 'notify_on_new_items', 'notify_on_price_drops'
            ),
            'classes': ('collapse',)
        }),
        ('Account Status', {
            'fields': ('is_banned', 'ban_reason', 'ban_expires'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'created_at', 'updated_at', 'last_login_ip'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name')
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'last_login', 'api_key', 'rating', 'rating_count')
    inlines = [UserProfileInline, UserTransactionInline, UserVerificationInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('profile')
        return queryset

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    get_full_name.short_description = 'Full Name'

    def balance(self, obj):
        return f"${obj.balance:.2f}"
    balance.admin_order_field = 'balance'

    def rating(self, obj):
        if obj.rating_count > 0:
            return f"{obj.rating:.1f} ({obj.rating_count})"
        return "No ratings"
    rating.admin_order_field = 'rating'

    actions = ['verify_users', 'ban_users', 'unban_users', 'regenerate_api_keys']

    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users have been verified.')
    verify_users.short_description = 'Verify selected users'

    def ban_users(self, request, queryset):
        updated = queryset.update(is_banned=True, ban_reason='Banned by admin')
        self.message_user(request, f'{updated} users have been banned.')
    ban_users.short_description = 'Ban selected users'

    def unban_users(self, request, queryset):
        updated = queryset.update(is_banned=False, ban_reason='', ban_expires=None)
        self.message_user(request, f'{updated} users have been unbanned.')
    unban_users.short_description = 'Unban selected users'

    def regenerate_api_keys(self, request, queryset):
        for user in queryset:
            user.regenerate_api_key()
        self.message_user(request, f'API keys regenerated for {queryset.count()} users.')
    regenerate_api_keys.short_description = 'Regenerate API keys for selected users'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'get_user_email', 'total_bids', 'total_wins', 'get_win_rate',
        'total_spent', 'seller_rating', 'created_at'
    )
    list_filter = ('timezone', 'language', 'currency', 'show_statistics')
    search_fields = ('user__email', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'get_win_rate', 'get_average_spent')

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Social Media', {
            'fields': ('website', 'facebook', 'twitter', 'instagram')
        }),
        ('Preferences', {
            'fields': ('timezone', 'language', 'currency')
        }),
        ('Statistics', {
            'fields': ('total_bids', 'total_wins', 'total_spent', 'total_earned', 'get_win_rate', 'get_average_spent')
        }),
        ('Seller Info', {
            'fields': ('seller_rating', 'seller_rating_count', 'total_items_sold')
        }),
        ('Privacy Settings', {
            'fields': ('show_email', 'show_phone', 'show_address', 'show_statistics')
        }),
    )

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'

    def get_win_rate(self, obj):
        return f"{obj.get_win_rate():.1f}%"
    get_win_rate.short_description = 'Win Rate'

    def get_average_spent(self, obj):
        return f"${obj.get_average_spent_per_win():.2f}"
    get_average_spent.short_description = 'Avg Spent per Win'


@admin.register(UserTransaction)
class UserTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'transaction_type', 'amount', 'status', 'description',
        'auction_item', 'created_at'
    )
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('user__email', 'user__username', 'description', 'reference_id')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Transaction Info', {
            'fields': ('user', 'transaction_type', 'amount', 'status', 'description', 'reference_id')
        }),
        ('Related Objects', {
            'fields': ('auction_item', 'bid')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'auction_item')

    actions = ['mark_completed', 'mark_failed']

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} transactions marked as completed.')
    mark_completed.short_description = 'Mark as completed'

    def mark_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} transactions marked as failed.')
    mark_failed.short_description = 'Mark as failed'


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'verification_type', 'status', 'verification_code',
        'expires_at', 'verified_at', 'created_at'
    )
    list_filter = ('verification_type', 'status', 'created_at', 'verified_at')
    search_fields = ('user__email', 'user__username', 'verification_code')
    readonly_fields = ('created_at', 'updated_at', 'verified_at', 'is_expired')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Verification Info', {
            'fields': ('user', 'verification_type', 'status', 'verification_code')
        }),
        ('Timing', {
            'fields': ('expires_at', 'verified_at', 'is_expired')
        }),
        ('Data', {
            'fields': ('verification_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

    actions = ['mark_verified', 'mark_rejected']

    def mark_verified(self, request, queryset):
        for verification in queryset:
            verification.mark_verified()
        self.message_user(request, f'{queryset.count()} verifications marked as verified.')
    mark_verified.short_description = 'Mark as verified'

    def mark_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} verifications marked as rejected.')
    mark_rejected.short_description = 'Mark as rejected'


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'from_user', 'to_user', 'feedback_type', 'rating', 'auction_item',
        'is_public', 'created_at'
    )
    list_filter = ('feedback_type', 'rating', 'is_public', 'created_at')
    search_fields = ('from_user__email', 'to_user__email', 'comment', 'auction_item__title')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Feedback Info', {
            'fields': ('from_user', 'to_user', 'feedback_type', 'rating', 'comment')
        }),
        ('Related', {
            'fields': ('auction_item', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('from_user', 'to_user', 'auction_item')

    actions = ['make_public', 'make_private']

    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} feedback items made public.')
    make_public.short_description = 'Make public'

    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} feedback items made private.')
    make_private.short_description = 'Make private'


# Admin site customization
admin.site.site_header = 'Auction Platform Administration'
admin.site.site_title = 'Auction Admin'
admin.site.index_title = 'Welcome to Auction Administration'
