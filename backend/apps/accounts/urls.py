from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.UserRegistrationAPIView.as_view(), name='register'),
    path('login/', views.UserLoginAPIView.as_view(), name='login'),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),

    # Profile Management
    path('profile/', views.UserProfileAPIView.as_view(), name='profile'),
    path('profile/update/', views.UserProfileAPIView.as_view(), name='profile_update'),

    # Balance Operations
    path('balance/', views.UserBalanceAPIView.as_view(), name='balance'),
    path('balance/add/', views.UserBalanceAPIView.as_view(), name='balance_add'),

    # Transaction History
    path('transactions/', views.UserTransactionAPIView.as_view(), name='transactions'),

    # Statistics
    path('statistics/', views.UserStatisticsAPIView.as_view(), name='statistics'),

    # API Key Management
    path('api-key/', views.APIKeyManagementView.as_view(), name='api_key'),
    path('verify-api-key/', views.verify_api_key, name='verify_api_key'),
    path('regenerate-api-key/', views.APIKeyManagementView.as_view(), name='regenerate_api_key'),

    # Telegram Integration
    path('link-telegram/', views.link_telegram_account, name='link_telegram'),

    # Utility endpoints
    path('user-exists/', views.user_exists, name='user_exists'),
    path('health/', views.health_check, name='health_check'),

    # Include router URLs
    path('', include(router.urls)),
]
