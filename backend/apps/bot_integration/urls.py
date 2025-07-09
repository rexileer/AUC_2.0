from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()

app_name = 'bot_integration'

urlpatterns = [
    # Bot User Management
    path('register/', views.BotUserRegistrationAPIView.as_view(), name='bot_user_register'),
    path('users/', views.BotUserListAPIView.as_view(), name='bot_user_list'),
    path('users/<str:telegram_id>/', views.BotUserDetailAPIView.as_view(), name='bot_user_detail'),
    path('users/<str:telegram_id>/link/', views.LinkUserAPIView.as_view(), name='link_user'),
    path('users/<str:telegram_id>/unlink/', views.UnlinkUserAPIView.as_view(), name='unlink_user'),

    # Bot Commands and Sessions
    path('commands/', views.BotCommandListAPIView.as_view(), name='command_list'),
    path('commands/create/', views.BotCommandCreateAPIView.as_view(), name='command_create'),
    path('commands/<uuid:pk>/', views.BotCommandDetailAPIView.as_view(), name='command_detail'),

    path('sessions/', views.BotSessionListAPIView.as_view(), name='session_list'),
    path('sessions/create/', views.BotSessionCreateAPIView.as_view(), name='session_create'),
    path('sessions/<uuid:pk>/', views.BotSessionDetailAPIView.as_view(), name='session_detail'),
    path('sessions/<uuid:pk>/complete/', views.CompleteBotSessionAPIView.as_view(), name='complete_session'),

    # Notification Settings
    path('notification-settings/', views.BotNotificationSettingsAPIView.as_view(), name='notification_settings'),
    path('notification-settings/update/', views.BotNotificationSettingsAPIView.as_view(), name='notification_settings_update'),
    path('toggle-notification/', views.ToggleNotificationAPIView.as_view(), name='toggle_notification'),

    # Bot Analytics
    path('analytics/', views.BotAnalyticsAPIView.as_view(), name='analytics'),
    path('analytics/daily/', views.DailyAnalyticsAPIView.as_view(), name='daily_analytics'),
    path('analytics/commands/', views.CommandAnalyticsAPIView.as_view(), name='command_analytics'),
    path('analytics/users/', views.UserAnalyticsAPIView.as_view(), name='user_analytics'),

    # Webhook Management
    path('webhooks/', views.BotWebhookListAPIView.as_view(), name='webhook_list'),
    path('webhooks/create/', views.BotWebhookCreateAPIView.as_view(), name='webhook_create'),
    path('webhooks/<uuid:pk>/', views.BotWebhookDetailAPIView.as_view(), name='webhook_detail'),
    path('webhooks/<uuid:pk>/process/', views.ProcessWebhookAPIView.as_view(), name='process_webhook'),

    # Bot Configuration
    path('config/', views.BotConfigurationListAPIView.as_view(), name='config_list'),
    path('config/<str:key>/', views.BotConfigurationDetailAPIView.as_view(), name='config_detail'),
    path('config/create/', views.BotConfigurationCreateAPIView.as_view(), name='config_create'),
    path('config/<str:key>/update/', views.BotConfigurationUpdateAPIView.as_view(), name='config_update'),

    # Bot Status and Health
    path('status/', views.BotStatusAPIView.as_view(), name='bot_status'),
    path('health/', views.bot_health_check, name='health_check'),

    # Bot Commands for Telegram Integration
    path('telegram/start/', views.TelegramStartCommandAPIView.as_view(), name='telegram_start'),
    path('telegram/balance/', views.TelegramBalanceCommandAPIView.as_view(), name='telegram_balance'),
    path('telegram/history/', views.TelegramHistoryCommandAPIView.as_view(), name='telegram_history'),
    path('telegram/items/', views.TelegramItemsCommandAPIView.as_view(), name='telegram_items'),
    path('telegram/notifications/', views.TelegramNotificationsCommandAPIView.as_view(), name='telegram_notifications'),

    # Statistics and Reports
    path('reports/', views.BotReportsAPIView.as_view(), name='reports'),
    path('reports/export/', views.ExportBotDataAPIView.as_view(), name='export_data'),

    # Utility endpoints
    path('validate-telegram-id/', views.ValidateTelegramIDAPIView.as_view(), name='validate_telegram_id'),
    path('send-test-message/', views.SendTestMessageAPIView.as_view(), name='send_test_message'),

    # Include router URLs
    path('', include(router.urls)),
]
