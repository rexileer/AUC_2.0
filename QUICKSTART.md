# 🚀 Quick Start Guide

Get your auction platform running in under 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Telegram Bot Token (optional, but recommended)

## 1. Clone & Setup

```bash
git clone <repository-url>
cd AUC_2.0
cp .env.example .env
```

## 2. Configure Environment

Edit `.env` file and set:

```env
# Required for bot functionality
BOT_TOKEN=your-telegram-bot-token-here

# Generate a secure secret key
SECRET_KEY=your-secure-secret-key-here

# Email settings (optional)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Get Telegram Bot Token:**
1. Message @BotFather on Telegram
2. Send `/newbot` command
3. Follow instructions and get your token

## 3. Start the Platform

```bash
./start.sh
```

That's it! The script will:
- Build all Docker containers
- Set up the database
- Create admin user (admin/admin123)
- Start all services

## 4. Access Your Platform

- **Website**: http://localhost
- **Admin Panel**: http://localhost/admin
- **API Docs**: http://localhost/api/docs/

## 5. Test the Bot

1. Find your bot on Telegram
2. Send `/start` command
3. Use `/input_api_key` to link your account
4. Get API key from: http://localhost/accounts/input_api_key/

## Default Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`
- ⚠️ Change these in production!

## Useful Commands

```bash
# View logs
docker-compose logs -f

# Stop platform
./start.sh stop

# Restart platform
./start.sh restart

# Clean everything
./start.sh clean
```

## Next Steps

1. 📝 Create your first auction at http://localhost/auctions/create/
2. 💰 Add balance to test bidding
3. 🤖 Set up bot notifications
4. 👥 Invite friends to test

## Troubleshooting

**Bot not working?**
- Check `BOT_TOKEN` in `.env`
- Run `docker-compose logs bot`

**Database issues?**
- Run `docker-compose down -v && ./start.sh`

**Need help?**
- Check full README.md
- View logs: `docker-compose logs`

---

🎉 **Enjoy your auction platform!**