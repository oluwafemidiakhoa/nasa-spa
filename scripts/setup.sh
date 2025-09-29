#!/bin/bash
# Setup script for NASA Space Weather Forecaster

set -e

echo "🌌 NASA Space Weather Forecaster Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Windows (Git Bash/WSL)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    print_warning "Detected Windows environment. Some commands may need adjustment."
fi

# Check prerequisites
print_status "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check Python (for development setup)
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    print_warning "Python is not installed. Docker-only deployment will be used."
    PYTHON_CMD=""
else
    PYTHON_CMD=$(command -v python3 || command -v python)
    print_status "Found Python at: $PYTHON_CMD"
fi

# Check Node.js (for development setup)
if ! command -v node &> /dev/null; then
    print_warning "Node.js is not installed. Docker-only deployment will be used."
    NODE_CMD=""
else
    NODE_CMD=$(command -v node)
    print_status "Found Node.js at: $NODE_CMD"
fi

print_status "Prerequisites check completed."

# Setup environment variables
print_status "Setting up environment configuration..."

if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cat > .env << 'EOL'
# NASA Space Weather Forecaster Environment Variables

# NASA API Key - Get from https://api.nasa.gov/
NASA_API_KEY=your_nasa_api_key_here

# Anthropic API Key - Get from https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Email Configuration (optional - for notifications)
EMAIL_USER=
EMAIL_PASSWORD=
FROM_EMAIL=

# SMS Configuration (optional - for notifications)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_PHONE=

# Test notification recipients
TEST_ALERT_EMAIL=
TEST_ALERT_PHONE=

# Database Configuration (production)
POSTGRES_PASSWORD=secure_postgres_password_change_this

# Domain (for production deployment)
DOMAIN=localhost

# Logging
LOG_LEVEL=INFO
EOL
    
    print_warning "Created .env file. Please edit it with your API keys:"
    echo "  1. Get NASA API key from: https://api.nasa.gov/"
    echo "  2. Get Anthropic API key from: https://console.anthropic.com/"
    echo "  3. Configure notification settings (optional)"
    read -p "Press Enter to continue after updating .env file..."
else
    print_status ".env file already exists"
fi

# Function to setup development environment
setup_development() {
    print_status "Setting up development environment..."
    
    if [ -n "$PYTHON_CMD" ]; then
        print_status "Installing Python dependencies..."
        $PYTHON_CMD -m pip install --upgrade pip
        $PYTHON_CMD -m pip install -r requirements.txt
        
        print_status "Running database initialization..."
        cd backend
        $PYTHON_CMD -c "
import asyncio
from database import DatabaseManager

async def init_db():
    db = DatabaseManager()
    await db.initialize()
    print('Database initialized successfully')

asyncio.run(init_db())
"
        cd ..
    fi
    
    if [ -n "$NODE_CMD" ]; then
        print_status "Installing Node.js dependencies..."
        cd web/nextjs
        npm install
        cd ../..
    fi
}

# Function to setup Docker environment
setup_docker() {
    print_status "Setting up Docker environment..."
    
    print_status "Building Docker images..."
    docker-compose build
    
    print_status "Creating Docker volumes..."
    docker volume create nasa-weather-backend-data 2>/dev/null || true
    
    print_status "Starting services..."
    docker-compose up -d
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    if docker-compose ps | grep -q "Up (healthy)"; then
        print_status "Services are running and healthy!"
    else
        print_warning "Some services may not be fully ready. Check with: docker-compose ps"
    fi
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    if [ -n "$PYTHON_CMD" ]; then
        print_status "Testing backend API..."
        $PYTHON_CMD -c "
import requests
import time

# Wait for service to be ready
for i in range(30):
    try:
        response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
        if response.status_code == 200:
            print('✓ Backend API is responding')
            break
    except:
        time.sleep(1)
else:
    print('✗ Backend API health check failed')

# Test forecast endpoint
try:
    response = requests.get('http://localhost:8000/api/v1/forecast/current', timeout=30)
    if response.status_code == 200:
        print('✓ Forecast endpoint is working')
    else:
        print(f'✗ Forecast endpoint returned status {response.status_code}')
except Exception as e:
    print(f'✗ Forecast endpoint test failed: {e}')
"
    fi
    
    print_status "Testing frontend..."
    curl -f http://localhost:3000 > /dev/null 2>&1 && \
        print_status "✓ Frontend is responding" || \
        print_warning "✗ Frontend health check failed"
}

# Main setup logic
print_status "Choose setup type:"
echo "  1. Development setup (Python + Node.js + Docker)"
echo "  2. Docker-only setup"
echo "  3. Production setup"
read -p "Enter choice (1-3): " SETUP_TYPE

case $SETUP_TYPE in
    1)
        print_status "Running development setup..."
        setup_development
        setup_docker
        ;;
    2)
        print_status "Running Docker-only setup..."
        setup_docker
        ;;
    3)
        print_status "Running production setup..."
        print_warning "Production setup requires additional configuration."
        print_status "Starting production services..."
        docker-compose -f docker-compose.prod.yml build
        docker-compose -f docker-compose.prod.yml up -d
        ;;
    *)
        print_error "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Run tests
if [ "$SETUP_TYPE" != "3" ]; then
    print_status "Running health checks..."
    sleep 5
    run_tests
fi

print_status "Setup completed!"
echo ""
print_status "Access your NASA Space Weather Dashboard:"
echo "  🌐 Web Dashboard: http://localhost:3000"
echo "  🔌 API Server: http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/docs"
echo ""
print_status "Useful commands:"
echo "  docker-compose ps                 # Check service status"
echo "  docker-compose logs -f            # View logs"
echo "  docker-compose down               # Stop services"
echo "  docker-compose up -d              # Start services"
echo ""
print_status "🚀 NASA Space Weather Forecaster is ready!"