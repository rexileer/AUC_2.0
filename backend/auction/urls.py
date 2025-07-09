from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

# API Router
router = DefaultRouter()

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication
    path('api/auth/', include('rest_framework.urls')),
    path('api/token/', obtain_auth_token, name='api_token_auth'),
    path('accounts/', include('allauth.urls')),

    # API Routes
    path('api/', include(router.urls)),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/auctions/', include('apps.auctions.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/bot/', include('apps.bot_integration.urls')),

    # Web Routes
    path('', include('apps.auctions.urls_web')),
    path('user/', include('apps.accounts.urls_web')),
    path('notify/', include('apps.notifications.urls_web')),




]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Add debug toolbar if available
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Custom error handlers
# handler404 = 'apps.auctions.views.custom_404'
# handler500 = 'apps.auctions.views.custom_500'

# Admin site customization
admin.site.site_header = 'Auction Administration'
admin.site.site_title = 'Auction Admin'
admin.site.index_title = 'Welcome to Auction Administration'
