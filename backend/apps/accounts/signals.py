from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import User, UserProfile, UserTransaction, UserVerification
from apps.notifications.models import Notification
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.info(f"Created profile for user {instance.username}")
        except Exception as e:
            logger.error(f"Error creating profile for user {instance.username}: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            # Create profile if it doesn't exist
            UserProfile.objects.create(user=instance)
    except Exception as e:
        logger.error(f"Error saving profile for user {instance.username}: {e}")


@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    """Send welcome notification to new users"""
    if created:
        try:
            # Create welcome notification
            Notification.objects.create(
                recipient=instance,
                notification_type='welcome',
                title='Welcome to Auction Platform!',
                message=f'Welcome {instance.get_full_name() or instance.username}! '
                       f'Your account has been created successfully. '
                       f'You can now start bidding on items or create your own auctions.',
                priority='normal'
            )
            logger.info(f"Welcome notification sent to {instance.username}")
        except Exception as e:
            logger.error(f"Error sending welcome notification to {instance.username}: {e}")


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """Send welcome email to new users"""
    if created and instance.email:
        try:
            # Send welcome email asynchronously
            from apps.accounts.tasks import send_welcome_email_task
            send_welcome_email_task.delay(instance.id)
            logger.info(f"Welcome email task queued for {instance.username}")
        except Exception as e:
            logger.error(f"Error queuing welcome email for {instance.username}: {e}")


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Handle user login events"""
    try:
        # Update last login IP
        if hasattr(request, 'META'):
            ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR')
            if ip:
                user.last_login_ip = ip.split(',')[0].strip()
                user.save(update_fields=['last_login_ip'])

        # Update profile last login
        if hasattr(user, 'profile'):
            user.profile.save()

        logger.info(f"User {user.username} logged in from IP: {user.last_login_ip}")
    except Exception as e:
        logger.error(f"Error handling login for user {user.username}: {e}")


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """Handle user logout events"""
    try:
        if user:
            logger.info(f"User {user.username} logged out")
    except Exception as e:
        logger.error(f"Error handling logout: {e}")


@receiver(post_save, sender=UserTransaction)
def update_user_balance(sender, instance, created, **kwargs):
    """Update user balance when transaction is completed"""
    if instance.status == 'completed' and created:
        try:
            user = instance.user

            # Update balance based on transaction type
            if instance.transaction_type in ['deposit', 'refund', 'bonus']:
                user.balance += instance.amount
            elif instance.transaction_type in ['withdraw', 'bid', 'payment', 'penalty']:
                user.balance -= instance.amount

            user.save(update_fields=['balance'])

            # Update profile statistics
            if hasattr(user, 'profile'):
                profile = user.profile
                if instance.transaction_type == 'deposit':
                    profile.total_spent += instance.amount
                elif instance.transaction_type == 'payment':
                    profile.total_earned += instance.amount
                profile.save(update_fields=['total_spent', 'total_earned'])

            logger.info(f"Updated balance for user {user.username}: {instance.transaction_type} ${instance.amount}")
        except Exception as e:
            logger.error(f"Error updating balance for transaction {instance.id}: {e}")


@receiver(post_save, sender=UserVerification)
def handle_verification_status(sender, instance, created, **kwargs):
    """Handle verification status changes"""
    if not created and instance.status == 'verified':
        try:
            user = instance.user

            # Update user verification status if all required verifications are complete
            required_verifications = ['email', 'phone']
            verified_types = user.verifications.filter(status='verified').values_list('verification_type', flat=True)

            if all(vtype in verified_types for vtype in required_verifications):
                user.is_verified = True
                user.save(update_fields=['is_verified'])

                # Send verification complete notification
                Notification.objects.create(
                    recipient=user,
                    notification_type='system',
                    title='Account Verified!',
                    message='Your account has been fully verified. You can now access all features.',
                    priority='normal'
                )

                logger.info(f"User {user.username} account fully verified")

        except Exception as e:
            logger.error(f"Error handling verification for user {instance.user.username}: {e}")


@receiver(pre_save, sender=User)
def handle_user_status_changes(sender, instance, **kwargs):
    """Handle user status changes (ban, suspension, etc.)"""
    if instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)

            # Handle ban status change
            if old_user.is_banned != instance.is_banned:
                if instance.is_banned:
                    # User was banned
                    Notification.objects.create(
                        recipient=instance,
                        notification_type='system',
                        title='Account Suspended',
                        message=f'Your account has been suspended. Reason: {instance.ban_reason or "Policy violation"}',
                        priority='high'
                    )
                    logger.warning(f"User {instance.username} was banned: {instance.ban_reason}")
                else:
                    # User was unbanned
                    Notification.objects.create(
                        recipient=instance,
                        notification_type='system',
                        title='Account Restored',
                        message='Your account has been restored. You can now access all features.',
                        priority='normal'
                    )
                    logger.info(f"User {instance.username} was unbanned")

            # Handle verification status change
            if old_user.is_verified != instance.is_verified and instance.is_verified:
                logger.info(f"User {instance.username} verification status changed to verified")

        except User.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error handling status change for user {instance.username}: {e}")


@receiver(post_delete, sender=User)
def handle_user_deletion(sender, instance, **kwargs):
    """Handle user account deletion"""
    try:
        logger.info(f"User {instance.username} account deleted")

        # Clean up related data if needed
        # Note: Most cleanup should be handled by CASCADE relationships

    except Exception as e:
        logger.error(f"Error handling deletion for user {instance.username}: {e}")


@receiver(post_save, sender=User)
def update_telegram_integration(sender, instance, **kwargs):
    """Update Telegram bot integration when user data changes"""
    if instance.telegram_user_id:
        try:
            # Update bot user if exists
            from apps.bot_integration.models import BotUser
            try:
                bot_user = BotUser.objects.get(telegram_id=instance.telegram_user_id)
                if not bot_user.user:
                    bot_user.link_user(instance)
                    logger.info(f"Linked Telegram user {instance.telegram_user_id} to {instance.username}")
            except BotUser.DoesNotExist:
                pass
        except Exception as e:
            logger.error(f"Error updating Telegram integration for {instance.username}: {e}")


@receiver(post_save, sender=UserProfile)
def update_user_statistics(sender, instance, created, **kwargs):
    """Update user statistics when profile is saved"""
    # Skip if this is just a profile creation or if we're already updating statistics
    if created or getattr(instance, '_updating_statistics', False):
        return

    try:
        user = instance.user

        # Update auction-related statistics
        from apps.auctions.models import Bid, AuctionItem

        # Update bid statistics
        bid_stats = Bid.objects.filter(bidder=user).aggregate(
            total_bids=models.Count('id'),
            total_spent=models.Sum('amount', filter=models.Q(status='won'))
        )

        total_bids = bid_stats['total_bids'] or 0
        total_spent = bid_stats['total_spent'] or 0

        # Update win statistics
        won_items = AuctionItem.objects.filter(winner=user).count()
        total_wins = won_items

        # Update seller statistics
        sold_items = AuctionItem.objects.filter(seller=user, status='sold').count()
        total_items_sold = sold_items

        # Calculate earnings
        earnings = AuctionItem.objects.filter(
            seller=user,
            status='sold'
        ).aggregate(
            total=models.Sum('current_price')
        )['total'] or 0

        total_earned = earnings

        # Use update() to avoid triggering post_save signal again
        UserProfile.objects.filter(id=instance.id).update(
            total_bids=total_bids,
            total_wins=total_wins,
            total_spent=total_spent,
            total_earned=total_earned,
            total_items_sold=total_items_sold
        )

    except Exception as e:
        logger.error(f"Error updating statistics for user {instance.user.username}: {e}")


# Import models for aggregation
from django.db import models
