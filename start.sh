#!/bin/bash

# Auction Platform 2.0 - Startup Script
# This script sets up and starts the entire auction platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    success "Docker and Docker Compose are installed"
}

# Check if environment file exists
check_env_file() {
    if [[ ! -f .env ]]; then
        warning "Environment file (.env) not found"
        if [[ -f .env.example ]]; then
            log "Copying .env.example to .env"
            cp .env.example .env
            warning "Please edit .env file with your configuration before continuing"
            echo ""
            echo "Required variables to set:"
            echo "- BOT_TOKEN (get from @BotFather on Telegram)"
            echo "- SECRET_KEY (generate a secure key)"
            echo "- EMAIL_* settings (if you want email notifications)"
            echo ""
            read -p "Press Enter when you've configured .env file..."
        else
            error ".env.example file not found. Cannot create environment file."
            exit 1
        fi
    fi
    success "Environment file found"
}

# Validate required environment variables
validate_env() {
    log "Validating environment variables..."

    # Source the .env file
    set -a
    source .env
    set +a

    # Check critical variables
    if [[ -z "$BOT_TOKEN" ]] || [[ "$BOT_TOKEN" == "your-telegram-bot-token-here" ]]; then
        warning "BOT_TOKEN not set or using default value"
        warning "Bot functionality will not work without a valid token"
    fi

    if [[ -z "$SECRET_KEY" ]] || [[ "$SECRET_KEY" == "your-secret-key-here" ]]; then
        warning "SECRET_KEY not set or using default value"
        warning "This is insecure for production use"
    fi

    success "Environment validation completed"
}

# Build and start Docker services
start_services() {
    log "Building and starting Docker services..."

    # Stop any existing services
    docker-compose down --remove-orphans

    # Build and start services
    docker-compose up -d --build

    success "Docker services started"
}

# Wait for services to be ready
wait_for_services() {
    log "Waiting for services to be ready..."

    # Wait for database
    log "Waiting for PostgreSQL..."
    until docker-compose exec -T db pg_isready -U auction_user -d auction_db; do
        sleep 2
    done
    success "PostgreSQL is ready"

    # Wait for Redis
    log "Waiting for Redis..."
    until docker-compose exec -T redis redis-cli ping; do
        sleep 2
    done
    success "Redis is ready"

    # Wait for RabbitMQ
    log "Waiting for RabbitMQ..."
    sleep 10  # RabbitMQ takes a bit longer to start
    success "RabbitMQ should be ready"

    # Wait for backend
    log "Waiting for Django backend..."
    sleep 15  # Give Django time to start
    success "Backend services are ready"
}

# Initialize database
init_database() {
    log "Initializing database..."

    # Run migrations
    log "Running database migrations..."
    docker-compose exec -T backend python manage.py migrate
    success "Database migrations completed"

    # Create superuser if it doesn't exist
    log "Creating superuser (if not exists)..."
    docker-compose exec -T backend python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

    # Load initial data if available
    if docker-compose exec -T backend test -f initial_data.json; then
        log "Loading initial data..."
        docker-compose exec -T backend python manage.py loaddata initial_data.json
        success "Initial data loaded"
    fi

    success "Database initialization completed"
}

# Collect static files
collect_static() {
    log "Collecting static files..."
    docker-compose exec -T backend python manage.py collectstatic --noinput
    success "Static files collected"
}

# Health check
health_check() {
    log "Performing health checks..."

    # Check if services are running
    if ! docker-compose ps | grep -q "Up"; then
        error "Some services are not running"
        docker-compose ps
        return 1
    fi

    # Check backend health
    log "Checking backend health..."
    sleep 5
    if curl -f http://localhost/health/ &> /dev/null; then
        success "Backend is healthy"
    else
        warning "Backend health check failed - this might be normal on first startup"
    fi

    # Check if bot is running
    if docker-compose logs bot 2>&1 | grep -q "Bot started" || docker-compose logs bot 2>&1 | grep -q "Starting bot"; then
        success "Telegram bot is running"
    else
        warning "Telegram bot might not be running properly"
    fi

    success "Health checks completed"
}

# Show access information
show_access_info() {
    echo ""
    echo "🎉 Auction Platform 2.0 is ready!"
    echo ""
    echo "📱 Access URLs:"
    echo "  Web Platform: http://localhost"
    echo "  Admin Panel:  http://localhost/admin"
    echo "  API Docs:     http://localhost/api/docs/"
    echo ""
    echo "🔐 Default Admin Credentials:"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo "  ⚠️  Change these in production!"
    echo ""
    echo "🤖 Telegram Bot:"
    echo "  Search for your bot on Telegram and start it with /start"
    echo "  Get your API key from: http://localhost/accounts/input_api_key/"
    echo ""
    echo "📊 Monitoring:"
    echo "  RabbitMQ: http://localhost:15672 (guest/guest)"
    echo ""
    echo "📝 Logs:"
    echo "  View logs: docker-compose logs -f"
    echo "  View backend logs: docker-compose logs -f backend"
    echo "  View bot logs: docker-compose logs -f bot"
    echo ""
}

# Stop services
stop_services() {
    log "Stopping all services..."
    docker-compose down
    success "All services stopped"
}

# Clean up (remove containers and volumes)
clean_up() {
    log "Cleaning up containers and volumes..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    success "Cleanup completed"
}

# Show help
show_help() {
    echo "Auction Platform 2.0 - Startup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the platform (default)"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  clean     Stop and remove all containers and volumes"
    echo "  logs      Show logs for all services"
    echo "  status    Show status of all services"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Start the platform"
    echo "  $0 start        # Start the platform"
    echo "  $0 stop         # Stop the platform"
    echo "  $0 restart      # Restart the platform"
    echo "  $0 clean        # Clean up everything"
    echo ""
}

# Main startup function
start_platform() {
    echo "🎯 Starting Auction Platform 2.0..."
    echo ""

    check_docker
    check_env_file
    validate_env
    start_services
    wait_for_services
    init_database
    collect_static
    health_check
    show_access_info
}

# Main script logic
main() {
    case "${1:-start}" in
        "start")
            start_platform
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            start_platform
            ;;
        "clean")
            clean_up
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "status")
            docker-compose ps
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Trap Ctrl+C
trap 'echo -e "\n\n⚠️  Script interrupted by user"; exit 1' INT

# Run main function
main "$@"
