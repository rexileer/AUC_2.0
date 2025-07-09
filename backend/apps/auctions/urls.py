from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()

app_name = 'auctions_api'

urlpatterns = [
    # Auction Items
    path('items/', views.AuctionItemListAPIView.as_view(), name='item_list'),
    path('items/create/', views.AuctionItemCreateAPIView.as_view(), name='item_create'),
    path('items/<int:pk>/', views.AuctionItemDetailAPIView.as_view(), name='item_detail'),
    path('items/<slug:slug>/', views.AuctionItemDetailAPIView.as_view(), name='item_detail_slug'),
    path('items/<int:pk>/update/', views.AuctionItemUpdateAPIView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.AuctionItemDeleteAPIView.as_view(), name='item_delete'),

    # Bidding
    path('items/<int:pk>/bid/', views.PlaceBidAPIView.as_view(), name='place_bid'),
    path('items/<int:pk>/bids/', views.ItemBidsAPIView.as_view(), name='item_bids'),
    path('bids/<int:pk>/', views.BidDetailAPIView.as_view(), name='bid_detail'),

    # User's Items and Bids
    path('my-items/', views.UserItemsAPIView.as_view(), name='my_items'),
    path('my-bids/', views.UserBidsAPIView.as_view(), name='my_bids'),
    path('my-wins/', views.UserWinsAPIView.as_view(), name='my_wins'),
    path('my-selling/', views.UserSellingAPIView.as_view(), name='my_selling'),

    # Watchlist
    path('watchlist/', views.WatchlistAPIView.as_view(), name='watchlist'),
    path('items/<int:pk>/watch/', views.ToggleWatchAPIView.as_view(), name='toggle_watch'),
    path('watching/', views.WatchingItemsAPIView.as_view(), name='watching_items'),

    # Categories
    path('categories/', views.CategoryListAPIView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailAPIView.as_view(), name='category_detail'),
    path('categories/<slug:slug>/', views.CategoryDetailAPIView.as_view(), name='category_detail_slug'),
    path('categories/<int:pk>/items/', views.CategoryItemsAPIView.as_view(), name='category_items'),

    # Comments and Questions
    path('items/<int:pk>/comments/', views.ItemCommentsAPIView.as_view(), name='item_comments'),
    path('comments/', views.CommentCreateAPIView.as_view(), name='comment_create'),
    path('comments/<int:pk>/', views.CommentDetailAPIView.as_view(), name='comment_detail'),
    path('comments/<int:pk>/reply/', views.CommentReplyAPIView.as_view(), name='comment_reply'),

    # Search and Filters
    path('search/', views.SearchItemsAPIView.as_view(), name='search_items'),
    path('filter/', views.FilterItemsAPIView.as_view(), name='filter_items'),
    path('saved-searches/', views.SavedSearchAPIView.as_view(), name='saved_searches'),

    # Statistics and Reports
    path('statistics/', views.AuctionStatisticsAPIView.as_view(), name='statistics'),
    path('trending/', views.TrendingItemsAPIView.as_view(), name='trending_items'),
    path('featured/', views.FeaturedItemsAPIView.as_view(), name='featured_items'),

    # Auction Management
    path('items/<int:pk>/end/', views.EndAuctionAPIView.as_view(), name='end_auction'),
    path('items/<int:pk>/extend/', views.ExtendAuctionAPIView.as_view(), name='extend_auction'),
    path('items/<int:pk>/cancel/', views.CancelAuctionAPIView.as_view(), name='cancel_auction'),

    # Reports
    path('items/<int:pk>/report/', views.ReportItemAPIView.as_view(), name='report_item'),
    path('reports/', views.UserReportsAPIView.as_view(), name='user_reports'),

    # Image Management
    path('items/<int:pk>/images/', views.ItemImagesAPIView.as_view(), name='item_images'),
    path('images/<int:pk>/', views.ImageDetailAPIView.as_view(), name='image_detail'),
    path('images/<int:pk>/delete/', views.DeleteImageAPIView.as_view(), name='delete_image'),

    # Auction History
    path('items/<int:pk>/history/', views.AuctionHistoryAPIView.as_view(), name='auction_history'),
    path('history/', views.UserAuctionHistoryAPIView.as_view(), name='user_auction_history'),

    # Bulk Operations
    path('bulk/watch/', views.BulkWatchAPIView.as_view(), name='bulk_watch'),
    path('bulk/unwatch/', views.BulkUnwatchAPIView.as_view(), name='bulk_unwatch'),

    # Health Check
    path('health/', views.auction_health_check, name='health_check'),

    # Include router URLs
    path('', include(router.urls)),
]
