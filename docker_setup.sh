#!/bin/bash
# NASA Space Weather Dashboard - Docker Setup Script

set -e

echo "🚀 NASA Space Weather Dashboard - Docker Setup"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p data logs ssl static
    print_success "Directories created"
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment file..."
    if [ ! -f .env ]; then
        cat > .env << EOF
# NASA Space Weather Dashboard Environment Configuration

# NASA API Configuration
NASA_API_KEY=your_nasa_api_key_here

# Anthropic AI Configuration  
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///data/spaceweather.db

# Redis Configuration
REDIS_URL=redis://redis:6379

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Security
SECRET_KEY=your_secret_key_here

# Logging
LOG_LEVEL=INFO
EOF
        print_warning "Created .env file with default values. Please update with your API keys!"
    else
        print_success "Environment file already exists"
    fi
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    docker-compose build --no-cache
    print_success "Docker images built successfully"
}

# Start services
start_services() {
    print_status "Starting NASA Space Weather Dashboard services..."
    docker-compose up -d
    print_success "Services started successfully"
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    if curl -f http://localhost/health > /dev/null 2>&1; then
        print_success "Services are healthy and ready!"
    else
        print_warning "Services may still be starting up..."
    fi
}

# Stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Services stopped"
}

# View logs
view_logs() {
    print_status "Viewing service logs..."
    docker-compose logs -f
}

# Show status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    
    echo ""
    print_status "Available endpoints:"
    echo "  🌐 Web Interface: http://localhost"
    echo "  📊 API Server: http://localhost/api"
    echo "  🔌 WebSocket: ws://localhost/ws"
    echo "  ❤️  Health Check: http://localhost/health"
}

# Main script logic
case "$1" in
    "setup")
        check_docker
        create_directories
        setup_environment
        build_images
        start_services
        show_status
        ;;
    "start")
        start_services
        show_status
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        start_services
        show_status
        ;;
    "logs")
        view_logs
        ;;
    "status")
        show_status
        ;;
    "build")
        build_images
        ;;
    *)
        echo "NASA Space Weather Dashboard - Docker Management"
        echo ""
        echo "Usage: $0 {setup|start|stop|restart|logs|status|build}"
        echo ""
        echo "Commands:"
        echo "  setup   - Initial setup and start all services"
        echo "  start   - Start all services"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - View service logs"
        echo "  status  - Show service status"
        echo "  build   - Rebuild Docker images"
        echo ""
        exit 1
        ;;
esac
