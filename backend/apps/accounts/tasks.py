from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q
from datetime import timedelta
import logging
import requests

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_welcome_email_task(self, user_id):
    """Send welcome email to new user"""
    try:
        user = User.objects.get(id=user_id)

        # Render email template
        html_message = render_to_string('emails/welcome_email.html', {
            'user': user,
            'site_name': 'Auction Platform',
            'login_url': f"{settings.SITE_URL}/accounts/login/",
            'api_key': user.api_key,
        })

        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject='Welcome to Auction Platform!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Welcome email sent to {user.email}")
        return f"Welcome email sent to {user.email}"

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return f"User with ID {user_id} not found"
    except Exception as exc:
        logger.error(f"Error sending welcome email to user {user_id}: {exc}")

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

        return f"Failed to send welcome email after {self.max_retries} retries"


@shared_task(bind=True, max_retries=3)
def send_verification_email_task(self, user_id, verification_type='email'):
    """Send verification email to user"""
    try:
        user = User.objects.get(id=user_id)

        # Get or create verification record
        from .models import UserVerification
        verification, created = UserVerification.objects.get_or_create(
            user=user,
            verification_type=verification_type,
            defaults={
                'verification_code': UserVerification.generate_code(),
                'expires_at': timezone.now() + timedelta(hours=24),
                'status': 'pending'
            }
        )

        if not created and verification.is_expired():
            # Generate new code if expired
            verification.verification_code = UserVerification.generate_code()
            verification.expires_at = timezone.now() + timedelta(hours=24)
            verification.status = 'pending'
            verification.save()

        # Render email template
        html_message = render_to_string('emails/verification_email.html', {
            'user': user,
            'verification': verification,
            'site_name': 'Auction Platform',
            'verify_url': f"{settings.SITE_URL}/accounts/verify/{verification.verification_code}/",
        })

        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject='Verify your email address',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Verification email sent to {user.email}")
        return f"Verification email sent to {user.email}"

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return f"User with ID {user_id} not found"
    except Exception as exc:
        logger.error(f"Error sending verification email to user {user_id}: {exc}")

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

        return f"Failed to send verification email after {self.max_retries} retries"


@shared_task
def cleanup_expired_verifications():
    """Clean up expired verification records"""
    try:
        from .models import UserVerification

        expired_verifications = UserVerification.objects.filter(
            expires_at__lt=timezone.now(),
            status='pending'
        )

        count = expired_verifications.count()
        expired_verifications.update(status='expired')

        logger.info(f"Cleaned up {count} expired verification records")
        return f"Cleaned up {count} expired verification records"

    except Exception as exc:
        logger.error(f"Error cleaning up expired verifications: {exc}")
        return f"Error cleaning up expired verifications: {exc}"


@shared_task
def update_user_statistics():
    """Update user statistics for all users"""
    try:
        from .models import UserProfile
        from apps.auctions.models import Bid, AuctionItem

        users_updated = 0

        for profile in UserProfile.objects.select_related('user'):
            user = profile.user

            # Update bid statistics
            bid_stats = Bid.objects.filter(bidder=user).aggregate(
                total_bids=Count('id'),
                total_spent=Sum('amount', filter=Q(status='won'))
            )

            profile.total_bids = bid_stats['total_bids'] or 0
            profile.total_spent = bid_stats['total_spent'] or 0

            # Update win statistics
            won_items = AuctionItem.objects.filter(winner=user).count()
            profile.total_wins = won_items

            # Update seller statistics
            sold_items = AuctionItem.objects.filter(seller=user, status='sold').count()
            profile.total_items_sold = sold_items

            # Calculate earnings
            earnings = AuctionItem.objects.filter(
                seller=user,
                status='sold'
            ).aggregate(
                total=Sum('current_price')
            )['total'] or 0

            profile.total_earned = earnings

            profile.save(update_fields=[
                'total_bids', 'total_wins', 'total_spent',
                'total_earned', 'total_items_sold'
            ])

            users_updated += 1

        logger.info(f"Updated statistics for {users_updated} users")
        return f"Updated statistics for {users_updated} users"

    except Exception as exc:
        logger.error(f"Error updating user statistics: {exc}")
        return f"Error updating user statistics: {exc}"


@shared_task
def send_password_reset_email_task(user_id, reset_token):
    """Send password reset email"""
    try:
        user = User.objects.get(id=user_id)

        # Render email template
        html_message = render_to_string('emails/password_reset_email.html', {
            'user': user,
            'reset_token': reset_token,
            'site_name': 'Auction Platform',
            'reset_url': f"{settings.SITE_URL}/accounts/reset-password/{reset_token}/",
        })

        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject='Password Reset Request',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Password reset email sent to {user.email}")
        return f"Password reset email sent to {user.email}"

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return f"User with ID {user_id} not found"
    except Exception as exc:
        logger.error(f"Error sending password reset email: {exc}")
        return f"Error sending password reset email: {exc}"


@shared_task
def process_user_registration(user_id):
    """Process new user registration"""
    try:
        user = User.objects.get(id=user_id)

        # Send welcome email
        send_welcome_email_task.delay(user_id)

        # Send verification email if email verification is required
        if not user.is_verified:
            send_verification_email_task.delay(user_id, 'email')

        # Create initial notification preferences
        from apps.notifications.models import NotificationPreference
        NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'enabled': True,
                'web_notifications': True,
                'email_notifications': True,
                'telegram_notifications': False,
            }
        )

        # Log registration
        logger.info(f"Processed registration for user {user.username}")
        return f"Processed registration for user {user.username}"

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return f"User with ID {user_id} not found"
    except Exception as exc:
        logger.error(f"Error processing user registration: {exc}")
        return f"Error processing user registration: {exc}"


@shared_task
def send_account_activity_email(user_id, activity_type, activity_data):
    """Send account activity notification email"""
    try:
        user = User.objects.get(id=user_id)

        if not user.email_notifications:
            return f"Email notifications disabled for user {user.username}"

        subject_mapping = {
            'login': 'New Login to Your Account',
            'password_changed': 'Password Changed',
            'email_changed': 'Email Address Changed',
            'profile_updated': 'Profile Updated',
            'api_key_regenerated': 'API Key Regenerated',
        }

        subject = subject_mapping.get(activity_type, 'Account Activity')

        # Render email template
        html_message = render_to_string('emails/account_activity_email.html', {
            'user': user,
            'activity_type': activity_type,
            'activity_data': activity_data,
            'site_name': 'Auction Platform',
        })

        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Account activity email sent to {user.email}")
        return f"Account activity email sent to {user.email}"

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return f"User with ID {user_id} not found"
    except Exception as exc:
        logger.error(f"Error sending account activity email: {exc}")
        return f"Error sending account activity email: {exc}"


@shared_task
def cleanup_inactive_users():
    """Clean up inactive users who haven't verified their accounts"""
    try:
        # Delete users who haven't verified their email within 30 days
        cutoff_date = timezone.now() - timedelta(days=30)

        inactive_users = User.objects.filter(
            is_active=True,
            is_verified=False,
            email_verified=False,
            created_at__lt=cutoff_date,
            last_login__isnull=True
        )

        count = inactive_users.count()
        inactive_users.delete()

        logger.info(f"Cleaned up {count} inactive unverified users")
        return f"Cleaned up {count} inactive unverified users"

    except Exception as exc:
        logger.error(f"Error cleaning up inactive users: {exc}")
        return f"Error cleaning up inactive users: {exc}"


@shared_task
def generate_user_report(user_id):
    """Generate comprehensive user report"""
    try:
        user = User.objects.get(id=user_id)

        # Gather user statistics
        from apps.auctions.models import Bid, AuctionItem
        from apps.notifications.models import Notification

        report_data = {
            'user_info': {
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'joined_date': user.created_at,
                'last_login': user.last_login,
                'is_verified': user.is_verified,
                'balance': float(user.balance),
                'rating': float(user.rating),
                'rating_count': user.rating_count,
            },
            'bidding_activity': {
                'total_bids': Bid.objects.filter(bidder=user).count(),
                'active_bids': Bid.objects.filter(bidder=user, status='active').count(),
                'won_auctions': AuctionItem.objects.filter(winner=user).count(),
                'total_spent': float(Bid.objects.filter(bidder=user, status='won').aggregate(
                    total=Sum('amount'))['total'] or 0),
            },
            'selling_activity': {
                'items_listed': AuctionItem.objects.filter(seller=user).count(),
                'items_sold': AuctionItem.objects.filter(seller=user, status='sold').count(),
                'total_earned': float(AuctionItem.objects.filter(
                    seller=user, status='sold').aggregate(
                    total=Sum('current_price'))['total'] or 0),
            },
            'notifications': {
                'total_received': Notification.objects.filter(recipient=user).count(),
                'unread_count': Notification.objects.filter(recipient=user, is_read=False).count(),
            }
        }

        logger.info(f"Generated report for user {user.username}")
        return report_data

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return f"User with ID {user_id} not found"
    except Exception as exc:
        logger.error(f"Error generating user report: {exc}")
        return f"Error generating user report: {exc}"


@shared_task
def sync_user_with_external_service(user_id, service_name):
    """Sync user data with external services"""
    try:
        user = User.objects.get(id=user_id)

        # Example: Sync with external CRM or analytics service
        if service_name == 'analytics':
            # Send user data to analytics service
            analytics_data = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'joined_date': user.created_at.isoformat(),
                'is_verified': user.is_verified,
                'total_bids': getattr(user, 'profile', {}).total_bids if hasattr(user, 'profile') else 0,
            }

            # Make API call to external service
            # requests.post('https://analytics-service.com/api/users', json=analytics_data)

        logger.info(f"Synced user {user.username} with {service_name}")
        return f"Synced user {user.username} with {service_name}"

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return f"User with ID {user_id} not found"
    except Exception as exc:
        logger.error(f"Error syncing user with external service: {exc}")
        return f"Error syncing user with external service: {exc}"


@shared_task
def backup_user_data(user_id):
    """Backup user data"""
    try:
        user = User.objects.get(id=user_id)

        # Create backup of user data
        backup_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'created_at': user.created_at.isoformat(),
                'balance': float(user.balance),
                'is_verified': user.is_verified,
            },
            'profile': {},
            'transactions': [],
            'verifications': [],
            'feedback': [],
        }

        # Add profile data
        if hasattr(user, 'profile'):
            profile = user.profile
            backup_data['profile'] = {
                'total_bids': profile.total_bids,
                'total_wins': profile.total_wins,
                'total_spent': float(profile.total_spent),
                'total_earned': float(profile.total_earned),
                'seller_rating': float(profile.seller_rating),
                'timezone': profile.timezone,
                'language': profile.language,
                'currency': profile.currency,
            }

        # Add transaction data
        for transaction in user.transactions.all():
            backup_data['transactions'].append({
                'type': transaction.transaction_type,
                'amount': float(transaction.amount),
                'status': transaction.status,
                'description': transaction.description,
                'created_at': transaction.created_at.isoformat(),
            })

        # Store backup data (in production, this would go to a backup service)
        logger.info(f"Created backup for user {user.username}")
        return f"Created backup for user {user.username}"

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return f"User with ID {user_id} not found"
    except Exception as exc:
        logger.error(f"Error backing up user data: {exc}")
        return f"Error backing up user data: {exc}"
