# AUC 2.0 Templates Documentation

This directory contains all HTML templates for the AUC 2.0 auction platform. The templates are organized by Django app and follow a modular, reusable design pattern.

## Structure Overview

```
templates/
├── base.html                    # Main base template
├── includes/                    # Reusable components
│   ├── navbar.html             # Navigation bar
│   ├── footer.html             # Site footer
│   └── messages.html           # Django messages display
├── accounts/                    # User account templates
│   ├── login.html              # Login page
│   ├── register.html           # Registration page
│   ├── dashboard.html          # User dashboard
│   └── profile.html            # User profile management
├── auctions/                    # Auction-related templates
│   ├── home.html               # Homepage
│   ├── auction_items.html      # Items listing page
│   ├── item_detail.html        # Individual item details
│   └── create_item.html        # Create auction form
└── notifications/               # Notification templates
    └── notifications.html       # Notifications page
```

## Base Template (`base.html`)

The main template that all other templates extend. Includes:

- **Meta tags**: SEO optimization, Open Graph, Twitter Cards
- **CSS frameworks**: Bootstrap 5, Font Awesome, Bootstrap Icons
- **JavaScript**: Bootstrap, WebSocket integration for real-time updates
- **Responsive design**: Mobile-first approach
- **Dark/Light theme support**: CSS variables for easy theming

### Key Features:
- CSRF token meta tag for AJAX requests
- Real-time notification system
- Responsive navigation
- Toast notification system
- WebSocket connection for live updates

## Includes Directory

### `navbar.html`
Responsive navigation bar with:
- User authentication state handling
- Balance display for logged-in users
- Real-time notification dropdown
- Search functionality
- Mobile-responsive hamburger menu
- Quick action buttons (Create Auction, etc.)

### `footer.html`
Site footer containing:
- Quick links organized by categories
- Social media links
- Contact information
- Copyright and branding
- Responsive grid layout

### `messages.html`
Django messages framework integration:
- Auto-dismissible alerts
- Different styling for message types (success, error, warning, info)
- Auto-hide after 5 seconds
- Smooth animations
- Mobile-responsive positioning

## Accounts Templates

### `login.html`
User login page featuring:
- Responsive login form
- Social login buttons (placeholder)
- Password reset link
- Registration link
- Benefits of creating an account
- Form validation and loading states

### `register.html`
User registration page with:
- Multi-step form layout
- Real-time password strength indicator
- Email/username availability checking
- Terms of service agreement
- Social registration options
- Welcome bonus information

### `dashboard.html`
User dashboard providing:
- Welcome header with user stats
- Balance display
- Quick action buttons
- Recent activity feed
- Active bids table
- Ending soon items
- Real-time data updates

### `profile.html`
Profile management page including:
- Avatar upload functionality
- Personal information editing
- Privacy settings with toggles
- Account verification status
- Recent activity history
- Quick action sidebar

## Auctions Templates

### `home.html`
Homepage template with:
- Hero section with call-to-action
- Featured auctions carousel
- Category browsing
- How it works section
- Live statistics
- Newsletter signup
- Animated elements and counters

### `auction_items.html`
Items listing page featuring:
- Advanced search and filtering
- Grid/List view toggle
- Sorting options
- Pagination
- Category sidebar
- Price range filter
- Real-time updates for bid counts and time remaining

### `item_detail.html`
Individual item page with:
- Image gallery with zoom functionality
- Bidding interface with real-time updates
- Countdown timer
- Bid history
- Seller information
- Comments section
- Similar items suggestions
- Watchlist functionality

### `create_item.html`
Auction creation form including:
- Multi-section form layout
- Image upload with drag & drop
- Price setting with validation
- Duration selection
- Shipping options
- Live preview
- Form validation and tips

## Notifications Templates

### `notifications.html`
Notifications management page with:
- Filter tabs (All, Unread, Bids, etc.)
- Bulk actions (mark as read, delete)
- Real-time updates
- Pagination
- Different notification types styling
- Empty state handling

## CSS Framework and Styling

All templates use:
- **Bootstrap 5**: For responsive grid and components
- **Font Awesome 6**: For icons
- **Custom CSS**: For auction-specific styling
- **CSS Variables**: For consistent theming
- **Responsive Design**: Mobile-first approach

### Color Scheme:
- Primary: #007bff (Bootstrap Blue)
- Success: #28a745 (Green for prices/wins)
- Warning: #ffc107 (Yellow for urgent items)
- Danger: #dc3545 (Red for alerts)

## JavaScript Features

### Real-time Updates:
- WebSocket integration for live bid updates
- Auto-refresh for countdown timers
- Real-time notification delivery
- Live user count and statistics

### Interactive Elements:
- Form validation and submission
- Image upload and preview
- Toggle switches for settings
- Infinite scroll (where applicable)
- Toast notifications

### AJAX Functionality:
- Watchlist toggle
- Bid placement
- Profile updates
- Notification management

## Template Extensions

### Extending Base Template:
```html
{% extends 'base.html' %}
{% load static %}

{% block title %}Your Page Title{% endblock %}

{% block extra_css %}
<style>
/* Your custom CSS */
</style>
{% endblock %}

{% block content %}
<!-- Your page content -->
{% endblock %}

{% block extra_js %}
<script>
// Your custom JavaScript
</script>
{% endblock %}
```

### Using Includes:
```html
<!-- Include navbar -->
{% include 'includes/navbar.html' %}

<!-- Include messages -->
{% include 'includes/messages.html' %}

<!-- Include footer -->
{% include 'includes/footer.html' %}
```

## Dependencies

### CSS Frameworks:
- Bootstrap 5.3.2
- Font Awesome 6.4.0
- Bootstrap Icons 1.11.1

### JavaScript Libraries:
- Bootstrap 5.3.2 JS
- WebSocket API (native)

### Django Template Tags:
- `{% load static %}`
- `{% csrf_token %}`
- Standard Django template filters

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Considerations

- Lazy loading for images
- Minified CSS and JavaScript
- Optimized WebSocket connections
- Efficient DOM manipulation
- Progressive enhancement

## Customization Guide

### Changing Colors:
Modify CSS variables in `base.html`:
```css
:root {
    --primary-color: #your-color;
    --secondary-color: #your-color;
}
```

### Adding New Pages:
1. Create template in appropriate app directory
2. Extend `base.html`
3. Add URL pattern
4. Include in navigation if needed

### Modifying Components:
- Edit files in `includes/` directory
- Changes apply to all templates using the include

## Security Features

- CSRF protection on all forms
- XSS prevention through template escaping
- Secure WebSocket connections
- Input validation and sanitization

## Accessibility

- Semantic HTML structure
- ARIA labels where appropriate
- Keyboard navigation support
- Screen reader compatibility
- High contrast support

## Development Notes

- All templates are mobile-first responsive
- Use semantic HTML5 elements
- Follow Django template best practices
- Include loading states for async operations
- Provide fallbacks for JavaScript-dependent features

For more detailed implementation examples, see the individual template files.