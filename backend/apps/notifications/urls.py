from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()

app_name = 'notifications'

urlpatterns = [
    # Notification Management
    path('', views.NotificationListAPIView.as_view(), name='notification_list'),
    path('<uuid:pk>/', views.NotificationDetailAPIView.as_view(), name='notification_detail'),
    path('<uuid:pk>/read/', views.MarkNotificationReadAPIView.as_view(), name='mark_read'),
    path('mark-all-read/', views.MarkAllReadAPIView.as_view(), name='mark_all_read'),
    path('unread-count/', views.UnreadCountAPIView.as_view(), name='unread_count'),

    # Notification Types
    path('web/', views.WebNotificationListAPIView.as_view(), name='web_notifications'),
    path('email/', views.EmailNotificationListAPIView.as_view(), name='email_notifications'),
    path('telegram/', views.TelegramNotificationListAPIView.as_view(), name='telegram_notifications'),

    # Notification Preferences
    path('preferences/', views.NotificationPreferencesAPIView.as_view(), name='preferences'),
    path('preferences/update/', views.NotificationPreferencesAPIView.as_view(), name='preferences_update'),

    # Bulk Operations (Admin)
    path('bulk/', views.BulkNotificationListAPIView.as_view(), name='bulk_list'),
    path('bulk/create/', views.BulkNotificationCreateAPIView.as_view(), name='bulk_create'),
    path('bulk/<int:pk>/', views.BulkNotificationDetailAPIView.as_view(), name='bulk_detail'),
    path('bulk/<int:pk>/send/', views.SendBulkNotificationAPIView.as_view(), name='bulk_send'),

    # Templates (Admin)
    path('templates/', views.NotificationTemplateListAPIView.as_view(), name='template_list'),
    path('templates/<int:pk>/', views.NotificationTemplateDetailAPIView.as_view(), name='template_detail'),
    path('templates/create/', views.NotificationTemplateCreateAPIView.as_view(), name='template_create'),

    # Statistics and Analytics
    path('statistics/', views.NotificationStatisticsAPIView.as_view(), name='statistics'),
    path('delivery-stats/', views.DeliveryStatisticsAPIView.as_view(), name='delivery_stats'),

    # WebSocket Management
    path('ws/token/', views.WebSocketTokenAPIView.as_view(), name='ws_token'),

    # Utility endpoints
    path('test/', views.TestNotificationAPIView.as_view(), name='test_notification'),
    path('health/', views.notification_health_check, name='health_check'),

    # Notification Actions
    path('<uuid:pk>/dismiss/', views.DismissNotificationAPIView.as_view(), name='dismiss'),
    path('<uuid:pk>/archive/', views.ArchiveNotificationAPIView.as_view(), name='archive'),
    path('clear-dismissed/', views.ClearDismissedAPIView.as_view(), name='clear_dismissed'),

    # Export and Import
    path('export/', views.ExportNotificationsAPIView.as_view(), name='export'),
    path('import/', views.ImportNotificationsAPIView.as_view(), name='import'),

    # Include router URLs
    path('', include(router.urls)),
]
