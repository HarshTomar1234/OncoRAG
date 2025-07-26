#!/bin/bash

# OncoPilot MCP System Deployment Script
# This script sets up the complete collection-centric MCP architecture

set -e

echo "🚀 OncoPilot MCP Deployment Script"
echo "=================================="

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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        cp .env.example .env
        print_warning "Please edit .env file with your API keys and configuration"
    fi
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p mongo-init
    
    print_success "Environment setup complete"
}

# Development deployment
deploy_development() {
    print_status "Deploying for development..."
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    pip install -r ../requirements.txt
    
    # Start services
    print_status "Starting services with Docker Compose..."
    docker-compose up -d
    
    print_success "Development deployment complete!"
    print_status "Services are starting up..."
    print_status "Web Service: http://localhost:8000"
    print_status "MongoDB: mongodb://localhost:27017"
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_services_health
}

# Production deployment
deploy_production() {
    print_status "Deploying for production..."
    
    # Build and start services
    print_status "Building and starting production services..."
    docker-compose -f docker-compose.yml up -d --build
    
    print_success "Production deployment complete!"
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 15
    
    # Check service health
    check_services_health
}

# Check services health
check_services_health() {
    print_status "Checking services health..."
    
    services=("web-service:8000" "cancer-agent:8001" "gene-agent:8002" "drug-agent:8003" "drug-india-agent:8004")
    
    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        
        if curl -f http://localhost:$port/health &> /dev/null; then
            print_success "$name is healthy"
        else
            print_warning "$name is not responding on port $port"
        fi
    done
}

# Test the deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Test main web service
    print_status "Testing web service..."
    response=$(curl -s http://localhost:8000/health)
    if echo "$response" | grep -q "healthy"; then
        print_success "Web service is working"
    else
        print_error "Web service test failed"
    fi
    
    # Test agents list
    print_status "Testing agents endpoint..."
    agents_response=$(curl -s http://localhost:8000/agents)
    if echo "$agents_response" | grep -q "CancerKnowledgeAgent"; then
        print_success "Agents endpoint is working"
    else
        print_error "Agents endpoint test failed"
    fi
    
    # Test sample query
    print_status "Testing sample query..."
    query_response=$(curl -s -X POST http://localhost:8000/chat \
        -H "Content-Type: application/json" \
        -d '{"query": "What are biomarkers for lung cancer?"}')
    
    if echo "$query_response" | grep -q "success"; then
        print_success "Sample query test passed"
    else
        print_warning "Sample query test failed - this might be due to empty database"
    fi
}

# Stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Services stopped"
}

# Remove services and volumes
cleanup() {
    print_status "Cleaning up services and volumes..."
    docker-compose down -v
    docker system prune -f
    print_success "Cleanup complete"
}

# Show logs
show_logs() {
    service=${1:-}
    if [ -z "$service" ]; then
        print_status "Showing all service logs..."
        docker-compose logs -f
    else
        print_status "Showing logs for $service..."
        docker-compose logs -f "$service"
    fi
}

# Show help
show_help() {
    echo "OncoPilot MCP Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev           Deploy for development"
    echo "  prod          Deploy for production"
    echo "  test          Test the deployment"
    echo "  stop          Stop all services"
    echo "  cleanup       Stop services and remove volumes"
    echo "  logs [service] Show logs (optionally for specific service)"
    echo "  health        Check service health"
    echo "  help          Show this help message"
    echo ""
    echo "Services:"
    echo "  - web-service          Main FastAPI application"
    echo "  - cancer-agent         Cancer Knowledge MCP Server"
    echo "  - gene-agent           Gene Knowledge MCP Server"
    echo "  - drug-agent           Drug Knowledge MCP Server"
    echo "  - drug-india-agent     Drug India Knowledge MCP Server"
    echo "  - pubmed-server        PubMed MCP Server"
    echo "  - clinicaltrials-server Clinical Trials MCP Server"
    echo "  - websearch-server     Web Search MCP Server"
    echo "  - mongodb              MongoDB Database"
}

# Main script logic
main() {
    case "${1:-help}" in
        "dev")
            check_prerequisites
            setup_environment
            deploy_development
            ;;
        "prod")
            check_prerequisites
            setup_environment
            deploy_production
            ;;
        "test")
            test_deployment
            ;;
        "stop")
            stop_services
            ;;
        "cleanup")
            cleanup
            ;;
        "logs")
            show_logs "$2"
            ;;
        "health")
            check_services_health
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@" 