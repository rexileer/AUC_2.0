from django.urls import path
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views

app_name = 'accounts_web'

# Simple placeholder views
def placeholder_view(request, *args, **kwargs):
    return render(request, 'base.html', {'page_title': 'Coming Soon'})

def ajax_placeholder(request, *args, **kwargs):
    return JsonResponse({'message': 'Feature not yet implemented'})

def verify_account(request, verification_code):
    return render(request, 'base.html', {'page_title': 'Account Verification'})

def input_api_key(request):
    return render(request, 'base.html', {'page_title': 'API Key'})

def regenerate_api_key(request):
    return redirect('accounts:input_api_key')

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='base.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', placeholder_view, name='register'),
    path('verify/<str:verification_code>/', verify_account, name='verify_account'),

    # Dashboard and Profile
    path('dashboard/', placeholder_view, name='dashboard'),
    path('profile/', placeholder_view, name='profile'),
    path('profile/edit/', placeholder_view, name='edit_profile'),

    # Settings and Security
    path('settings/', placeholder_view, name='settings'),
    path('settings/password/', placeholder_view, name='change_password'),
    path('settings/notifications/', placeholder_view, name='notification_settings'),
    path('settings/privacy/', placeholder_view, name='privacy_settings'),

    # Balance and Transactions
    path('balance/', placeholder_view, name='balance'),
    path('balance/add/', placeholder_view, name='add_balance'),
    path('transactions/', placeholder_view, name='transaction_history'),
    path('transactions/<int:pk>/', placeholder_view, name='transaction_detail'),

    # API Key Management
    path('api-key/', placeholder_view, name='api_key'),
    path('input_api_key/', input_api_key, name='input_api_key'),
    path('regenerate-api-key/', regenerate_api_key, name='regenerate_api_key'),

    # Telegram Integration
    path('telegram/', placeholder_view, name='telegram_integration'),
    path('telegram/link/', placeholder_view, name='link_telegram'),
    path('telegram/unlink/', placeholder_view, name='unlink_telegram'),

    # Account History and Activity
    path('history/', placeholder_view, name='history'),
    path('activity/', placeholder_view, name='activity'),

    # Verification and Security
    path('verification/', placeholder_view, name='verification'),
    path('verification/phone/', placeholder_view, name='phone_verification'),
    path('verification/identity/', placeholder_view, name='identity_verification'),

    # Feedback and Reviews
    path('feedback/', placeholder_view, name='feedback_list'),
    path('feedback/give/<int:user_id>/', placeholder_view, name='give_feedback'),
    path('feedback/<int:pk>/', placeholder_view, name='feedback_detail'),

    # Account Management
    path('delete/', placeholder_view, name='delete_account'),
    path('export/', placeholder_view, name='export_data'),

    # AJAX endpoints for web interface
    path('ajax/check-username/', ajax_placeholder, name='ajax_check_username'),
    path('ajax/check-email/', ajax_placeholder, name='ajax_check_email'),
    path('ajax/upload-avatar/', ajax_placeholder, name='ajax_upload_avatar'),
    path('ajax/update-notifications/', ajax_placeholder, name='ajax_update_notifications'),
    path('ajax/get-balance/', ajax_placeholder, name='ajax_get_balance'),

    # Help and Support
    path('help/', placeholder_view, name='help'),
    path('contact/', placeholder_view, name='contact'),
    path('faq/', placeholder_view, name='faq'),
]
