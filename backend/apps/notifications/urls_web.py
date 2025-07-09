from django.urls import path
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView

app_name = 'notifications_web'

# Simple placeholder views
def placeholder_view(request, *args, **kwargs):
    return render(request, 'base.html', {'page_title': 'Notifications - Coming Soon'})

def ajax_placeholder(request, *args, **kwargs):
    return JsonResponse({'message': 'Feature not yet implemented'})

urlpatterns = [
    # Main notification pages
    path('', placeholder_view, name='list'),
    path('unread/', placeholder_view, name='unread'),
    path('read/', placeholder_view, name='read'),
    path('<uuid:pk>/', placeholder_view, name='detail'),

    # Notification actions
    path('<uuid:pk>/read/', placeholder_view, name='mark_read'),
    path('<uuid:pk>/unread/', placeholder_view, name='mark_unread'),
    path('<uuid:pk>/delete/', placeholder_view, name='delete'),
    path('mark-all-read/', placeholder_view, name='mark_all_read'),
    path('clear-all/', placeholder_view, name='clear_all'),

    # Notification preferences
    path('preferences/', placeholder_view, name='preferences'),
    path('preferences/edit/', placeholder_view, name='edit_preferences'),

    # Notification types
    path('web/', placeholder_view, name='web_notifications'),
    path('email/', placeholder_view, name='email_notifications'),
    path('telegram/', placeholder_view, name='telegram_notifications'),

    # Bulk notification management (Admin)
    path('admin/', placeholder_view, name='admin_panel'),
    path('admin/create/', placeholder_view, name='create_bulk'),
    path('admin/bulk/<int:pk>/', placeholder_view, name='bulk_detail'),
    path('admin/bulk/<int:pk>/send/', placeholder_view, name='send_bulk'),
    path('admin/templates/', placeholder_view, name='templates'),
    path('admin/templates/create/', placeholder_view, name='create_template'),
    path('admin/templates/<int:pk>/', placeholder_view, name='template_detail'),

    # Statistics and analytics
    path('statistics/', placeholder_view, name='statistics'),
    path('delivery-stats/', placeholder_view, name='delivery_stats'),

    # Settings and configuration
    path('settings/', placeholder_view, name='settings'),
    path('settings/channels/', placeholder_view, name='channel_settings'),
    path('settings/quiet-hours/', placeholder_view, name='quiet_hours'),

    # AJAX endpoints for real-time updates
    path('ajax/count/', ajax_placeholder, name='ajax_count'),
    path('ajax/latest/', ajax_placeholder, name='ajax_latest'),
    path('ajax/mark-read/<uuid:pk>/', ajax_placeholder, name='ajax_mark_read'),
    path('ajax/mark-all-read/', ajax_placeholder, name='ajax_mark_all_read'),
    path('ajax/delete/<uuid:pk>/', ajax_placeholder, name='ajax_delete'),
    path('ajax/toggle-preference/', ajax_placeholder, name='ajax_toggle_preference'),
    path('ajax/test-notification/', ajax_placeholder, name='ajax_test_notification'),

    # Export and import
    path('export/', placeholder_view, name='export'),
    path('import/', placeholder_view, name='import'),

    # Help and documentation
    path('help/', placeholder_view, name='help'),
    path('troubleshooting/', placeholder_view, name='troubleshooting'),
]
