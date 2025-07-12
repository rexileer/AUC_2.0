from django.urls import path  # type: ignore
from django.shortcuts import render  # type: ignore
from django.http import JsonResponse  # type: ignore

from .views import home_view, create_item_view, item_detail_view, search_view

app_name = 'auctions'

def items_view(request):
    """Placeholder view for listing auction items."""
    return render(request, 'items.html', {'page_title': 'Auction Items'})

def placeholder_view(request, *args, **kwargs):
    """Generic placeholder for pages not yet implemented."""
    return JsonResponse({'message': 'Feature not yet implemented'})

def ajax_placeholder(request, *args, **kwargs):
    """Generic placeholder for AJAX endpoints."""
    return JsonResponse({'message': 'Feature not yet implemented'})

urlpatterns = [
    # Home and listing pages
    path('', home_view, name='home'),
    path('auctions/', items_view, name='items'),
    path('create/', create_item_view, name='create_item'),
    path('item/<int:pk>/', item_detail_view, name='item_detail'),
    path('item/<slug:slug>/', item_detail_view, name='item_detail_slug'),
    path('search/', search_view, name='search'),

    # Item management
    path('item/<int:pk>/edit/', placeholder_view, name='edit_item'),
    path('item/<int:pk>/delete/', placeholder_view, name='delete_item'),

    # Bidding & watch
    path('item/<int:pk>/bid/', placeholder_view, name='place_bid'),
    path('item/<int:pk>/watch/', placeholder_view, name='toggle_watch'),

    # Categories
    path('categories/', placeholder_view, name='categories'),
    path('category/<int:pk>/', placeholder_view, name='category'),
    path('category/<slug:slug>/', placeholder_view, name='category_slug'),

    # User-specific pages
    path('my-items/', placeholder_view, name='my_items'),
    path('my-bids/', placeholder_view, name='my_bids'),
    path('my-wins/', placeholder_view, name='my_wins'),
    path('watchlist/', placeholder_view, name='watchlist'),

    # Comments
    path('item/<int:pk>/comment/', placeholder_view, name='add_comment'),
    path('comment/<int:pk>/reply/', placeholder_view, name='reply_comment'),

    # Feature highlights
    path('featured/', placeholder_view, name='featured'),
    path('trending/', placeholder_view, name='trending'),
    path('ending-soon/', placeholder_view, name='ending_soon'),

    # Reporting
    path('item/<int:pk>/report/', placeholder_view, name='report_item'),

    # AJAX endpoints
    path('ajax/item/<int:pk>/bid/', ajax_placeholder, name='ajax_place_bid'),
    path('ajax/item/<int:pk>/watch/', ajax_placeholder, name='ajax_toggle_watch'),
    path('ajax/search/', ajax_placeholder, name='ajax_search'),
    path('ajax/load-more-items/', ajax_placeholder, name='ajax_load_more'),

    # Static informational pages
    path('how-it-works/', placeholder_view, name='how_it_works'),
    path('terms/', placeholder_view, name='terms'),
    path('privacy/', placeholder_view, name='privacy'),
]
