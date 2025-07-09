# 🎯 Auction Platform 2.0

A comprehensive online auction platform with Django backend, Telegram bot integration, and real-time notifications.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Telegram Bot](#telegram-bot)
- [Usage](#usage)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🌐 Web Platform
- **User Management**: Registration, authentication, profile management
- **Auction System**: Create, bid on, and manage auction items
- **Real-time Updates**: WebSocket notifications for live bidding
- **Category System**: Hierarchical item categorization
- **Image Gallery**: Multiple images per auction item
- **Comment System**: Q&A between buyers and sellers
- **Watchlist**: Save and track interesting items
- **Rating System**: User feedback and reputation
- **Advanced Search**: Filters, saved searches, and recommendations

### 🤖 Telegram Bot
- **Account Linking**: Secure API key integration
- **Balance Management**: Check and add funds
- **Auction History**: View bids and won items
- **Item Browsing**: Paginated item listings with inline keyboards
- **Notifications**: Real-time auction updates
- **Profile Management**: View statistics and settings

### 🔔 Notification System
- **Multi-channel**: Web, Email, and Telegram notifications
- **Real-time**: WebSocket-powered live updates
- **Customizable**: User preferences for notification types
- **Bulk Admin**: Mass notifications from admin panel
- **Smart Filtering**: Quiet hours and frequency limits

### 🛡️ Admin Features
- **Comprehensive Dashboard**: User and auction management
- **Bulk Operations**: Mass user actions and notifications
- **Analytics**: Detailed statistics and reports
- **Content Moderation**: Report handling and user management
- **System Configuration**: Bot settings and templates

## 🛠️ Tech Stack

### Backend
- **Django 4.2** - Web framework
- **Django REST Framework** - API development
- **Django Channels** - WebSocket support
- **PostgreSQL** - Primary database
- **Redis** - Caching and sessions
- **RabbitMQ** - Message broker
- **Celery** - Background tasks

### Frontend
- **Bootstrap 5** - UI framework
- **JavaScript** - Real-time features
- **WebSocket** - Live notifications

### Bot
- **aiogram 3.1** - Telegram bot framework
- **httpx** - HTTP client
- **asyncio** - Async operations

### Infrastructure
- **Docker** - Containerization
- **Nginx** - Reverse proxy
- **WhiteNoise** - Static file serving

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Telegram Bot Token (from @BotFather)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AUC_2.0
```

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Initialize Database
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### 5. Access the Platform
- **Web**: http://localhost
- **Admin**: http://localhost/admin
- **API Docs**: http://localhost/api/docs

## 🔧 Detailed Setup

### 1. Environment Configuration

Create `.env` file from template:
```bash
cp .env.example .env
```

Key environment variables:
```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://auction_user:auction_password@db:5432/auction_db

# Redis & RabbitMQ
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://auction_user:auction_password@rabbitmq:5672/

# Telegram Bot
BOT_TOKEN=your-telegram-bot-token

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 2. Telegram Bot Setup

1. **Create Bot**:
   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Get your bot token

2. **Configure Bot**:
   - Add token to `.env` file
   - Set bot commands (automatic on startup)

3. **Test Bot**:
   - Start with `/start` command
   - Link account using `/input_api_key`

### 3. Database Setup

```bash
# Apply migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Load initial data (optional)
docker-compose exec backend python manage.py loaddata initial_data.json
```

### 4. Static Files
```bash
# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput
```

## 📡 API Documentation

### Authentication
All API endpoints require authentication via:
- **Token Auth**: `Authorization: Token <your-token>`
- **JWT**: `Authorization: Bearer <jwt-token>`
- **API Key**: `Authorization: Bearer <api-key>` (for bot)

### Main Endpoints

#### Authentication
```
POST /api/accounts/register/     # User registration
POST /api/accounts/login/        # User login
POST /api/accounts/logout/       # User logout
```

#### User Management
```
GET  /api/accounts/profile/      # Get user profile
PUT  /api/accounts/profile/      # Update profile
GET  /api/accounts/balance/      # Get balance
POST /api/accounts/balance/      # Add balance
GET  /api/accounts/transactions/ # Transaction history
```

#### Auctions
```
GET  /api/auctions/items/        # List auction items
POST /api/auctions/items/        # Create auction
GET  /api/auctions/items/{id}/   # Get item details
POST /api/auctions/items/{id}/bid/ # Place bid
GET  /api/auctions/my-bids/      # User's bids
GET  /api/auctions/my-items/     # User's items
```

#### Notifications
```
GET  /api/notifications/         # Get notifications
POST /api/notifications/mark-read/ # Mark as read
GET  /api/notifications/settings/ # Get preferences
PUT  /api/notifications/settings/ # Update preferences
```

### Interactive API Documentation
- **Swagger UI**: http://localhost/api/docs/
- **ReDoc**: http://localhost/api/redoc/
- **OpenAPI Schema**: http://localhost/api/schema/

## 🤖 Telegram Bot

### Commands
- `/start` - Welcome message and account linking
- `/input_api_key` - Link your auction account
- `/balance` - Check your current balance
- `/history` - View bids and won auctions
- `/get_items` - Browse auction items (paginated)
- `/turn_notifications` - Toggle notification settings
- `/my_bids` - View your active bids
- `/watching` - Items you're watching
- `/profile` - View your profile and statistics

### Features
- **Inline Keyboards**: Interactive buttons for navigation
- **Pagination**: Browse items with next/prev buttons
- **Real-time Updates**: Instant notifications
- **Secure Linking**: API key-based authentication
- **Rich Formatting**: HTML-formatted messages

### Bot Setup for Users
1. Get API key from website settings
2. Start bot with `/start`
3. Use `/input_api_key` and send your API key
4. Bot is now linked to your account

## 💻 Usage

### For Buyers
1. **Register**: Create account on website
2. **Add Funds**: Add money to your balance
3. **Browse**: Find items you want to bid on
4. **Bid**: Place bids on active auctions
5. **Watch**: Add items to watchlist
6. **Win**: Pay for won auctions

### For Sellers
1. **Verify**: Complete account verification
2. **Create**: List new auction items
3. **Manage**: Monitor bids and questions
4. **Complete**: Finalize successful sales

### For Admins
1. **Dashboard**: Monitor platform activity
2. **Users**: Manage user accounts and verification
3. **Auctions**: Oversee auction listings
4. **Notifications**: Send bulk messages
5. **Reports**: Handle user reports

## 🔧 Development

### Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd AUC_2.0

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
cd backend
pip install -r requirements.txt

# Setup database
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Bot Development
```bash
cd bot

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BOT_TOKEN=your-token
export BACKEND_URL=http://localhost:8000

# Run bot
python bot.py
```

### Running Tests
```bash
# Backend tests
docker-compose exec backend python manage.py test

# Bot tests
cd bot
pytest
```

### Code Quality
```bash
# Format code
black backend/
isort backend/

# Lint code
flake8 backend/
pylint backend/

# Type checking
mypy backend/
```

## 📊 Monitoring

### Logs
```bash
# View all logs
docker-compose logs

# View specific service
docker-compose logs backend
docker-compose logs bot
docker-compose logs nginx

# Follow logs
docker-compose logs -f backend
```

### Health Checks
- **Backend**: http://localhost/health/
- **Database**: Check through Django admin
- **Redis**: `docker-compose exec redis redis-cli ping`
- **RabbitMQ**: http://localhost:15672 (guest/guest)

### Metrics
- **Celery**: Flower monitoring at http://localhost:5555
- **Postgres**: Built-in statistics
- **Nginx**: Access and error logs

## 🚢 Production Deployment

### Security Checklist
- [ ] Change all default passwords
- [ ] Set strong SECRET_KEY
- [ ] Configure SSL/HTTPS
- [ ] Set up proper firewall rules
- [ ] Enable rate limiting
- [ ] Configure backup strategy
- [ ] Set up monitoring

### Environment Changes
```env
DEBUG=0
ALLOWED_HOSTS=your-domain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### SSL Setup
```bash
# Using Let's Encrypt
certbot --nginx -d your-domain.com
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### Coding Standards
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Write comprehensive tests
- Document complex functions
- Update README for new features

### Issue Reporting
- Use issue templates
- Provide clear reproduction steps
- Include system information
- Add relevant logs/screenshots

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- **API Docs**: Available at `/api/docs/`
- **Admin Guide**: Check admin interface help
- **User Guide**: Available on website

### Getting Help
- **Issues**: GitHub Issues for bugs
- **Discussions**: GitHub Discussions for questions
- **Email**: [Your support email]

### FAQ

**Q: How do I reset my API key?**
A: Go to Settings → API Key → Regenerate

**Q: Bot not responding?**
A: Check if bot token is correct and bot is running

**Q: Real-time notifications not working?**
A: Ensure WebSocket connection and Redis are working

**Q: Email notifications not sending?**
A: Check email configuration in settings

---

## 🎉 Quick Start Commands

```bash
# Complete setup in one go
git clone <repository-url>
cd AUC_2.0
cp .env.example .env
# Edit .env with your values
docker-compose up -d
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

**That's it! Your auction platform is ready! 🚀**

Visit http://localhost to start using the platform.