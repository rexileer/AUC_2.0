from django.urls import path, include
from .views import (
    AuctionItemListAPIView,
    AuctionItemCreateAPIView,
    AuctionItemDetailAPIView,
    AuctionItemUpdateAPIView,
    AuctionItemDeleteAPIView,
    PlaceBidAPIView,
    ItemBidsAPIView,
    BidDetailAPIView,
    UserItemsAPIView,
    UserBidsAPIView,
    UserWinsAPIView,
    UserSellingAPIView,
    WatchlistAPIView,
    ToggleWatchAPIView,
    WatchingItemsAPIView,
    CategoryListAPIView,
    CategoryDetailAPIView,
    CategoryItemsAPIView,
    ItemCommentsAPIView,
    CommentCreateAPIView,
    CommentDetailAPIView,
    CommentReplyAPIView,
    SearchItemsAPIView,
    FilterItemsAPIView,
    SavedSearchAPIView,
    AuctionStatisticsAPIView,
    TrendingItemsAPIView,
    FeaturedItemsAPIView,
    EndAuctionAPIView,
    ExtendAuctionAPIView,
    CancelAuctionAPIView,
    ReportItemAPIView,
    UserReportsAPIView,
    ItemImagesAPIView,
    ImageDetailAPIView,
    DeleteImageAPIView,
    AuctionHistoryAPIView,
    UserAuctionHistoryAPIView,
    BulkWatchAPIView,
    BulkUnwatchAPIView,
    auction_health_check
)

# API Router
urlpatterns = [
    # Auction Items
    path('items/', AuctionItemListAPIView.as_view(), name='item_list'),
    path('items/create/', AuctionItemCreateAPIView.as_view(), name='item_create'),
    path('items/<int:pk>/', AuctionItemDetailAPIView.as_view(), name='item_detail'),
    path('items/<slug:slug>/', AuctionItemDetailAPIView.as_view(), name='item_detail_slug'),
    path('items/<int:pk>/update/', AuctionItemUpdateAPIView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', AuctionItemDeleteAPIView.as_view(), name='item_delete'),

    # Bidding
    path('items/<int:pk>/bid/', PlaceBidAPIView.as_view(), name='place_bid'),
    path('items/<int:pk>/bids/', ItemBidsAPIView.as_view(), name='item_bids'),
    path('bids/<int:pk>/', BidDetailAPIView.as_view(), name='bid_detail'),

    # User's Items and Bids
    path('my-items/', UserItemsAPIView.as_view(), name='my_items'),
    path('my-bids/', UserBidsAPIView.as_view(), name='my_bids'),
    path('my-wins/', UserWinsAPIView.as_view(), name='my_wins'),
    path('my-selling/', UserSellingAPIView.as_view(), name='my_selling'),

    # Watchlist
    path('watchlist/', WatchlistAPIView.as_view(), name='watchlist'),
    path('items/<int:pk>/watch/', ToggleWatchAPIView.as_view(), name='toggle_watch'),
    path('watching/', WatchingItemsAPIView.as_view(), name='watching_items'),

    # Categories
    path('categories/', CategoryListAPIView.as_view(), name='category_list'),
    path('categories/<int:pk>/', CategoryDetailAPIView.as_view(), name='category_detail'),
    path('categories/<slug:slug>/', CategoryDetailAPIView.as_view(), name='category_detail_slug'),
    path('categories/<int:pk>/items/', CategoryItemsAPIView.as_view(), name='category_items'),

    # Comments and Questions
    path('items/<int:pk>/comments/', ItemCommentsAPIView.as_view(), name='item_comments'),
    path('comments/', CommentCreateAPIView.as_view(), name='comment_create'),
    path('comments/<int:pk>/', CommentDetailAPIView.as_view(), name='comment_detail'),
    path('comments/<int:pk>/reply/', CommentReplyAPIView.as_view(), name='comment_reply'),

    # Search and Filters
    path('search/', SearchItemsAPIView.as_view(), name='search_items'),
    path('filter/', FilterItemsAPIView.as_view(), name='filter_items'),
    path('saved-searches/', SavedSearchAPIView.as_view(), name='saved_searches'),

    # Statistics and Reports
    path('statistics/', AuctionStatisticsAPIView.as_view(), name='statistics'),
    path('trending/', TrendingItemsAPIView.as_view(), name='trending_items'),
    path('featured/', FeaturedItemsAPIView.as_view(), name='featured_items'),

    # Auction Management
    path('items/<int:pk>/end/', EndAuctionAPIView.as_view(), name='end_auction'),
    path('items/<int:pk>/extend/', ExtendAuctionAPIView.as_view(), name='extend_auction'),
    path('items/<int:pk>/cancel/', CancelAuctionAPIView.as_view(), name='cancel_auction'),

    # Reports
    path('items/<int:pk>/report/', ReportItemAPIView.as_view(), name='report_item'),
    path('reports/', UserReportsAPIView.as_view(), name='user_reports'),

    # Image Management
    path('items/<int:pk>/images/', ItemImagesAPIView.as_view(), name='item_images'),
    path('images/<int:pk>/', ImageDetailAPIView.as_view(), name='image_detail'),
    path('images/<int:pk>/delete/', DeleteImageAPIView.as_view(), name='delete_image'),

    # Auction History
    path('items/<int:pk>/history/', AuctionHistoryAPIView.as_view(), name='auction_history'),
    path('history/', UserAuctionHistoryAPIView.as_view(), name='user_auction_history'),

    # Bulk Operations
    path('bulk/watch/', BulkWatchAPIView.as_view(), name='bulk_watch'),
    path('bulk/unwatch/', BulkUnwatchAPIView.as_view(), name='bulk_unwatch'),

    # Health Check
    path('health/', auction_health_check, name='health_check'),
]
