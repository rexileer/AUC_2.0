from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models import User, UserProfile, UserTransaction, UserVerification, UserFeedback


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""

    win_rate = serializers.SerializerMethodField()
    average_spent_per_win = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'website', 'facebook', 'twitter', 'instagram',
            'timezone', 'language', 'currency',
            'total_bids', 'total_wins', 'total_spent', 'total_earned',
            'seller_rating', 'seller_rating_count', 'total_items_sold',
            'show_email', 'show_phone', 'show_address', 'show_statistics',
            'win_rate', 'average_spent_per_win'
        ]
        read_only_fields = [
            'total_bids', 'total_wins', 'total_spent', 'total_earned',
            'seller_rating', 'seller_rating_count', 'total_items_sold',
            'win_rate', 'average_spent_per_win'
        ]

    def get_win_rate(self, obj):
        """Calculate win rate percentage"""
        return obj.get_win_rate()

    def get_average_spent_per_win(self, obj):
        """Calculate average amount spent per win"""
        return float(obj.get_average_spent_per_win())


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    notification_preferences = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'display_name', 'avatar', 'bio', 'phone_number',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'balance', 'is_verified', 'rating', 'rating_count',
            'telegram_user_id', 'telegram_username',
            'email_notifications', 'telegram_notifications', 'web_notifications',
            'notify_on_bid', 'notify_on_outbid', 'notify_on_auction_end',
            'notify_on_auction_win', 'notify_on_new_items', 'notify_on_price_drops',
            'is_seller', 'is_banned', 'created_at', 'last_login',
            'profile', 'notification_preferences'
        ]
        read_only_fields = [
            'id', 'balance', 'rating', 'rating_count', 'is_verified',
            'is_banned', 'created_at', 'last_login', 'full_name',
            'display_name', 'notification_preferences'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'password': {'write_only': True},
        }

    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name()

    def get_display_name(self, obj):
        """Get user's display name"""
        return obj.get_display_name()

    def get_notification_preferences(self, obj):
        """Get user's notification preferences"""
        return obj.get_notification_preferences()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'phone_number',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password and password confirmation don't match")
        return attrs

    def validate_email(self, value):
        """Validate email uniqueness"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value

    def validate_username(self, value):
        """Validate username uniqueness"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User with this username already exists")
        return value

    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate user credentials"""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password")
            if not user.is_active:
                raise serializers.ValidationError("User account is inactive")
            if user.is_banned:
                raise serializers.ValidationError(f"User account is banned: {user.ban_reason}")
        else:
            raise serializers.ValidationError("Must include email and password")

        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

    def validate(self, attrs):
        """Validate new password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New password and confirmation don't match")
        return attrs

    def save(self):
        """Save new password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserTransactionSerializer(serializers.ModelSerializer):
    """Serializer for UserTransaction model"""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    auction_item_title = serializers.CharField(source='auction_item.title', read_only=True)
    bid_amount = serializers.DecimalField(source='bid.amount', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = UserTransaction
        fields = [
            'id', 'user', 'user_email', 'transaction_type', 'amount', 'status',
            'description', 'reference_id', 'auction_item', 'auction_item_title',
            'bid', 'bid_amount', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'auction_item_title', 'bid_amount',
            'created_at', 'updated_at'
        ]


class UserVerificationSerializer(serializers.ModelSerializer):
    """Serializer for UserVerification model"""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = UserVerification
        fields = [
            'id', 'user', 'user_email', 'verification_type', 'status',
            'verification_code', 'verification_data', 'expires_at',
            'verified_at', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'verification_code', 'verified_at',
            'is_expired', 'created_at', 'updated_at'
        ]

    def get_is_expired(self, obj):
        """Check if verification is expired"""
        return obj.is_expired()


class UserFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for UserFeedback model"""

    from_user_name = serializers.CharField(source='from_user.get_display_name', read_only=True)
    to_user_name = serializers.CharField(source='to_user.get_display_name', read_only=True)
    auction_item_title = serializers.CharField(source='auction_item.title', read_only=True)

    class Meta:
        model = UserFeedback
        fields = [
            'id', 'from_user', 'from_user_name', 'to_user', 'to_user_name',
            'feedback_type', 'rating', 'comment', 'auction_item',
            'auction_item_title', 'is_public', 'created_at'
        ]
        read_only_fields = [
            'id', 'from_user_name', 'to_user_name', 'auction_item_title',
            'created_at'
        ]

    def validate_rating(self, value):
        """Validate rating range"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate(self, attrs):
        """Validate feedback constraints"""
        from_user = attrs.get('from_user')
        to_user = attrs.get('to_user')
        auction_item = attrs.get('auction_item')
        feedback_type = attrs.get('feedback_type')

        if from_user == to_user:
            raise serializers.ValidationError("Cannot leave feedback for yourself")

        # Check if feedback already exists
        if UserFeedback.objects.filter(
            from_user=from_user,
            to_user=to_user,
            auction_item=auction_item,
            feedback_type=feedback_type
        ).exists():
            raise serializers.ValidationError("Feedback already exists for this item and type")

        return attrs


class UserStatisticsSerializer(serializers.Serializer):
    """Serializer for user statistics"""

    user_info = serializers.DictField()
    bidding = serializers.DictField()
    selling = serializers.DictField()
    feedback = serializers.DictField(required=False)

    class Meta:
        fields = ['user_info', 'bidding', 'selling', 'feedback']


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list view"""

    full_name = serializers.SerializerMethodField()
    total_items_sold = serializers.SerializerMethodField()
    win_rate = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'avatar', 'rating', 'rating_count',
            'is_verified', 'is_seller', 'total_items_sold', 'win_rate',
            'created_at', 'last_login'
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name()

    def get_total_items_sold(self, obj):
        """Get total items sold"""
        if hasattr(obj, 'profile'):
            return obj.profile.total_items_sold
        return 0

    def get_win_rate(self, obj):
        """Get win rate"""
        if hasattr(obj, 'profile'):
            return obj.profile.get_win_rate()
        return 0


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for user detail view"""

    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    recent_feedback = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'display_name', 'avatar', 'bio',
            'rating', 'rating_count', 'is_verified', 'is_seller',
            'created_at', 'last_login', 'profile', 'recent_feedback'
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name()

    def get_display_name(self, obj):
        """Get user's display name"""
        return obj.get_display_name()

    def get_recent_feedback(self, obj):
        """Get recent feedback for user"""
        recent_feedback = UserFeedback.objects.filter(
            to_user=obj,
            is_public=True
        ).order_by('-created_at')[:5]

        return UserFeedbackSerializer(recent_feedback, many=True).data


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for user update"""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'avatar', 'bio', 'phone_number',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'email_notifications', 'telegram_notifications', 'web_notifications',
            'notify_on_bid', 'notify_on_outbid', 'notify_on_auction_end',
            'notify_on_auction_win', 'notify_on_new_items', 'notify_on_price_drops'
        ]

    def validate_email(self, value):
        """Validate email uniqueness"""
        user = self.instance
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value


class BalanceSerializer(serializers.Serializer):
    """Serializer for balance operations"""

    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False)

    def validate_amount(self, value):
        """Validate amount"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        if value > 10000:  # Maximum single transaction
            raise serializers.ValidationError("Amount cannot exceed $10,000")
        return value


class APIKeySerializer(serializers.Serializer):
    """Serializer for API key operations"""

    api_key = serializers.CharField(read_only=True)
    telegram_linked = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ['api_key', 'telegram_linked']


class TelegramLinkSerializer(serializers.Serializer):
    """Serializer for Telegram account linking"""

    api_key = serializers.CharField()
    telegram_user_id = serializers.CharField()
    telegram_username = serializers.CharField(required=False)

    def validate_api_key(self, value):
        """Validate API key"""
        if not User.objects.filter(api_key=value).exists():
            raise serializers.ValidationError("Invalid API key")
        return value

    def validate_telegram_user_id(self, value):
        """Validate Telegram user ID"""
        if not value.isdigit():
            raise serializers.ValidationError("Invalid Telegram user ID")
        return value


class NotificationPreferencesSerializer(serializers.Serializer):
    """Serializer for notification preferences"""

    email_notifications = serializers.BooleanField()
    telegram_notifications = serializers.BooleanField()
    web_notifications = serializers.BooleanField()
    notify_on_bid = serializers.BooleanField()
    notify_on_outbid = serializers.BooleanField()
    notify_on_auction_end = serializers.BooleanField()
    notify_on_auction_win = serializers.BooleanField()
    notify_on_new_items = serializers.BooleanField()
    notify_on_price_drops = serializers.BooleanField()

    class Meta:
        fields = [
            'email_notifications', 'telegram_notifications', 'web_notifications',
            'notify_on_bid', 'notify_on_outbid', 'notify_on_auction_end',
            'notify_on_auction_win', 'notify_on_new_items', 'notify_on_price_drops'
        ]


class UserExportSerializer(serializers.ModelSerializer):
    """Serializer for user data export"""

    profile = UserProfileSerializer(read_only=True)
    transactions = UserTransactionSerializer(many=True, read_only=True)
    verifications = UserVerificationSerializer(many=True, read_only=True)
    feedback_received = UserFeedbackSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'bio', 'phone_number', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country', 'balance',
            'is_verified', 'rating', 'rating_count', 'created_at',
            'profile', 'transactions', 'verifications', 'feedback_received'
        ]
        read_only_fields = fields
