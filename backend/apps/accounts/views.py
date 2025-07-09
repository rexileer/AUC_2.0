from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, UpdateView, ListView
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.conf import settings
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
import json
import logging

from .models import User, UserProfile, UserTransaction, UserVerification, UserFeedback
from .serializers import (
    UserSerializer, UserProfileSerializer, UserTransactionSerializer,
    UserRegistrationSerializer, UserLoginSerializer, PasswordChangeSerializer,
    UserVerificationSerializer, UserFeedbackSerializer
)
from .forms import (
    UserRegistrationForm, UserProfileForm, PasswordChangeForm,
    UserVerificationForm, BalanceAddForm
)
from .tasks import send_verification_email_task, send_account_activity_email

logger = logging.getLogger(__name__)


# API Views
class UserRegistrationAPIView(APIView):
    """API view for user registration"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Create authentication token
            token, created = Token.objects.get_or_create(user=user)

            # Send verification email
            send_verification_email_task.delay(user.id, 'email')

            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'User registered successfully. Please check your email for verification.'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginAPIView(APIView):
    """API view for user login"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(username=email, password=password)
            if user:
                if user.is_active:
                    if not user.is_banned:
                        # Create or get token
                        token, created = Token.objects.get_or_create(user=user)

                        # Update last login IP
                        user.last_login_ip = request.META.get('REMOTE_ADDR')
                        user.save(update_fields=['last_login_ip'])

                        return Response({
                            'user': UserSerializer(user).data,
                            'token': token.key,
                            'message': 'Login successful'
                        })
                    else:
                        return Response({
                            'error': 'Account is banned',
                            'ban_reason': user.ban_reason
                        }, status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({
                        'error': 'Account is inactive'
                    }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """API view for user logout"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logout user and delete token"""
        try:
            # Delete the user's token
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()

            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return Response({
                'error': 'Logout failed'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    """API view for user profile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user profile"""
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)

        return Response({
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data
        })

    def put(self, request):
        """Update user profile"""
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)

        # Update user fields
        user_data = request.data.get('user', {})
        if user_data:
            user_serializer = UserSerializer(user, data=user_data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()
            else:
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Update profile fields
        profile_data = request.data.get('profile', {})
        if profile_data:
            profile_serializer = UserProfileSerializer(profile, data=profile_data, partial=True)
            if profile_serializer.is_valid():
                profile_serializer.save()
            else:
                return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data,
            'message': 'Profile updated successfully'
        })


class UserBalanceAPIView(APIView):
    """API view for user balance operations"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user balance"""
        user = request.user
        return Response({
            'balance': float(user.balance),
            'currency': 'USD'
        })

    def post(self, request):
        """Add balance (deposit)"""
        user = request.user
        amount = request.data.get('amount')

        if not amount:
            return Response({
                'error': 'Amount is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return Response({
                    'error': 'Amount must be positive'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create transaction
            transaction = UserTransaction.objects.create(
                user=user,
                transaction_type='deposit',
                amount=amount,
                status='completed',
                description=f'Balance deposit of ${amount}'
            )

            # Update balance
            user.add_balance(amount)

            return Response({
                'balance': float(user.balance),
                'transaction': UserTransactionSerializer(transaction).data,
                'message': f'Successfully added ${amount} to your balance'
            })

        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid amount format'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserTransactionAPIView(APIView):
    """API view for user transactions"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user transaction history"""
        user = request.user

        # Get query parameters
        transaction_type = request.query_params.get('type')
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 20))

        # Build queryset
        transactions = UserTransaction.objects.filter(user=user)

        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)

        transactions = transactions.order_by('-created_at')

        # Paginate
        paginator = Paginator(transactions, per_page)
        page_obj = paginator.get_page(page)

        return Response({
            'transactions': UserTransactionSerializer(page_obj, many=True).data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginator.count,
                'pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })


class UserStatisticsAPIView(APIView):
    """API view for user statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user statistics"""
        user = request.user

        # Get statistics
        from apps.auctions.models import Bid, AuctionItem

        bid_stats = Bid.objects.filter(bidder=user).aggregate(
            total_bids=Count('id'),
            active_bids=Count('id', filter=Q(status='active')),
            won_bids=Count('id', filter=Q(status='won'))
        )

        item_stats = AuctionItem.objects.filter(seller=user).aggregate(
            total_items=Count('id'),
            active_items=Count('id', filter=Q(status='active')),
            sold_items=Count('id', filter=Q(status='sold'))
        )

        return Response({
            'user_info': {
                'username': user.username,
                'email': user.email,
                'balance': float(user.balance),
                'rating': float(user.rating),
                'rating_count': user.rating_count,
                'is_verified': user.is_verified,
                'joined_date': user.created_at
            },
            'bidding': {
                'total_bids': bid_stats['total_bids'] or 0,
                'active_bids': bid_stats['active_bids'] or 0,
                'won_bids': bid_stats['won_bids'] or 0
            },
            'selling': {
                'total_items': item_stats['total_items'] or 0,
                'active_items': item_stats['active_items'] or 0,
                'sold_items': item_stats['sold_items'] or 0
            }
        })


class APIKeyManagementView(APIView):
    """API view for API key management"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user API key"""
        user = request.user
        return Response({
            'api_key': user.api_key,
            'telegram_linked': bool(user.telegram_user_id)
        })

    def post(self, request):
        """Regenerate API key"""
        user = request.user
        old_key = user.api_key
        new_key = user.regenerate_api_key()

        # Send notification
        send_account_activity_email.delay(
            user.id,
            'api_key_regenerated',
            {'old_key': old_key[:8] + '...', 'new_key': new_key[:8] + '...'}
        )

        return Response({
            'api_key': new_key,
            'message': 'API key regenerated successfully'
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_api_key(request):
    """Verify API key for bot integration"""
    api_key = request.data.get('api_key')

    if not api_key:
        return Response({
            'error': 'API key is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(api_key=api_key)
        return Response({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'balance': float(user.balance),
                'is_verified': user.is_verified
            }
        })
    except User.DoesNotExist:
        return Response({
            'valid': False,
            'error': 'Invalid API key'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def link_telegram_account(request):
    """Link Telegram account to user"""
    api_key = request.data.get('api_key')
    telegram_user_id = request.data.get('telegram_user_id')
    telegram_username = request.data.get('telegram_username')

    if not all([api_key, telegram_user_id]):
        return Response({
            'error': 'API key and Telegram user ID are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(api_key=api_key)

        # Check if Telegram account is already linked
        if User.objects.filter(telegram_user_id=telegram_user_id).exclude(id=user.id).exists():
            return Response({
                'error': 'Telegram account is already linked to another user'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Link Telegram account
        user.telegram_user_id = telegram_user_id
        user.telegram_username = telegram_username
        user.save()

        return Response({
            'success': True,
            'message': 'Telegram account linked successfully'
        })

    except User.DoesNotExist:
        return Response({
            'error': 'Invalid API key'
        }, status=status.HTTP_404_NOT_FOUND)


# Web Views
class DashboardView(LoginRequiredMixin, TemplateView):
    """User dashboard view"""
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get recent transactions
        recent_transactions = UserTransaction.objects.filter(
            user=user
        ).order_by('-created_at')[:5]

        # Get recent bids
        from apps.auctions.models import Bid
        recent_bids = Bid.objects.filter(
            bidder=user
        ).order_by('-created_at')[:5]

        # Get active auctions
        from apps.auctions.models import AuctionItem
        active_auctions = AuctionItem.objects.filter(
            seller=user,
            status='active'
        ).order_by('-created_at')[:5]

        context.update({
            'recent_transactions': recent_transactions,
            'recent_bids': recent_bids,
            'active_auctions': active_auctions,
        })

        return context


class ProfileView(LoginRequiredMixin, UpdateView):
    """User profile view"""
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = '/accounts/profile/'

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class TransactionHistoryView(LoginRequiredMixin, ListView):
    """Transaction history view"""
    model = UserTransaction
    template_name = 'accounts/transaction_history.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        return UserTransaction.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class BalanceView(LoginRequiredMixin, TemplateView):
    """Balance management view"""
    template_name = 'accounts/balance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['balance_form'] = BalanceAddForm()
        return context

    def post(self, request, *args, **kwargs):
        form = BalanceAddForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']

            # Create transaction
            transaction = UserTransaction.objects.create(
                user=request.user,
                transaction_type='deposit',
                amount=amount,
                status='completed',
                description=f'Balance deposit of ${amount}'
            )

            # Update balance
            request.user.add_balance(amount)

            messages.success(request, f'Successfully added ${amount} to your balance!')
            return redirect('accounts:balance')

        return render(request, self.template_name, {'balance_form': form})


class SettingsView(LoginRequiredMixin, TemplateView):
    """Account settings view"""
    template_name = 'accounts/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update({
            'password_form': PasswordChangeForm(),
            'api_key': user.api_key,
            'telegram_linked': bool(user.telegram_user_id),
        })

        return context


@login_required
def regenerate_api_key(request):
    """Regenerate API key"""
    if request.method == 'POST':
        user = request.user
        old_key = user.api_key
        new_key = user.regenerate_api_key()

        # Send notification
        send_account_activity_email.delay(
            user.id,
            'api_key_regenerated',
            {'old_key': old_key[:8] + '...', 'new_key': new_key[:8] + '...'}
        )

        messages.success(request, 'API key regenerated successfully!')
        return redirect('accounts:settings')

    return redirect('accounts:settings')


@login_required
def input_api_key(request):
    """Input API key page for bot integration"""
    return render(request, 'accounts/input_api_key.html', {
        'api_key': request.user.api_key,
        'telegram_linked': bool(request.user.telegram_user_id)
    })


# Auth Views
def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Send verification email
            send_verification_email_task.delay(user.id, 'email')

            messages.success(request, 'Account created successfully! Please check your email for verification.')
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user:
            if user.is_active:
                if not user.is_banned:
                    login(request, user)

                    # Update last login IP
                    user.last_login_ip = request.META.get('REMOTE_ADDR')
                    user.save(update_fields=['last_login_ip'])

                    next_url = request.GET.get('next', '/dashboard/')
                    return redirect(next_url)
                else:
                    messages.error(request, f'Account is banned: {user.ban_reason}')
            else:
                messages.error(request, 'Account is inactive')
        else:
            messages.error(request, 'Invalid email or password')

    return render(request, 'accounts/login.html')


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('accounts:login')


@csrf_exempt
def verify_account(request, verification_code):
    """Verify user account"""
    try:
        verification = UserVerification.objects.get(
            verification_code=verification_code,
            status='pending'
        )

        if verification.is_expired():
            messages.error(request, 'Verification code has expired')
            return redirect('accounts:login')

        # Mark as verified
        verification.mark_verified()

        messages.success(request, 'Account verified successfully!')
        return redirect('accounts:login')

    except UserVerification.DoesNotExist:
        messages.error(request, 'Invalid verification code')
        return redirect('accounts:login')


# Utility Views
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def user_exists(request):
    """Check if user exists by email"""
    email = request.query_params.get('email')
    if not email:
        return Response({
            'error': 'Email parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    exists = User.objects.filter(email=email).exists()
    return Response({
        'exists': exists
    })
