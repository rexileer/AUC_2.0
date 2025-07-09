from django.urls import path
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView

app_name = 'auctions'

# Simple placeholder views
def home_view(request):
    return render(request, 'base.html', {'page_title': 'Home'})

def items_view(request):
    return render(request, 'base.html', {'page_title': 'Auction Items'})

def placeholder_view(request, *args, **kwargs):
    return render(request, 'base.html', {'page_title': 'Coming Soon'})

def ajax_placeholder(request, *args, **kwargs):
    return JsonResponse({'message': 'Feature not yet implemented'})

urlpatterns = [
    # Home and main pages
    path('', home_view, name='home'),
    path('auctions/', items_view, name='items'),
    path('search/', placeholder_view, name='search'),

    # Item pages
    path('item/<int:pk>/', placeholder_view, name='item_detail'),
    path('item/<slug:slug>/', placeholder_view, name='item_detail_slug'),
    path('create/', placeholder_view, name='create_item'),
    path('item/<int:pk>/edit/', placeholder_view, name='edit_item'),
    path('item/<int:pk>/delete/', placeholder_view, name='delete_item'),

    # Bidding
    path('item/<int:pk>/bid/', placeholder_view, name='place_bid'),
    path('item/<int:pk>/watch/', placeholder_view, name='toggle_watch'),

    # Categories
    path('categories/', placeholder_view, name='categories'),
    path('category/<int:pk>/', placeholder_view, name='category'),
    path('category/<slug:slug>/', placeholder_view, name='category_slug'),

    # User pages
    path('my-items/', placeholder_view, name='my_items'),
    path('my-bids/', placeholder_view, name='my_bids'),
    path('my-wins/', placeholder_view, name='my_wins'),
    path('watchlist/', placeholder_view, name='watchlist'),

    # Comments and Questions
    path('item/<int:pk>/comment/', placeholder_view, name='add_comment'),
    path('comment/<int:pk>/reply/', placeholder_view, name='reply_comment'),

    # Advanced features
    path('featured/', placeholder_view, name='featured'),
    path('trending/', placeholder_view, name='trending'),
    path('ending-soon/', placeholder_view, name='ending_soon'),

    # Reports and moderation
    path('item/<int:pk>/report/', placeholder_view, name='report_item'),

    # AJAX endpoints for web interface
    path('ajax/item/<int:pk>/bid/', ajax_placeholder, name='ajax_place_bid'),
    path('ajax/item/<int:pk>/watch/', ajax_placeholder, name='ajax_toggle_watch'),
    path('ajax/search/', ajax_placeholder, name='ajax_search'),
    path('ajax/load-more-items/', ajax_placeholder, name='ajax_load_more'),

    # Static pages
    path('how-it-works/', placeholder_view, name='how_it_works'),
    path('terms/', placeholder_view, name='terms'),
    path('privacy/', placeholder_view, name='privacy'),
]
