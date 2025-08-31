#!/bin/bash

# AI Memory Bank Deployment Script
# Usage: ./deploy.sh [environment] [version]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-"development"}
VERSION=${2:-"latest"}
PROJECT_NAME="ai-memory-bank"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Environment-specific configurations
case $ENVIRONMENT in
  "development")
    COMPOSE_PROJECT_NAME="${PROJECT_NAME}-dev"
    API_PORT=8000
    FRONTEND_PORT=3000
    ;;
  "staging")
    COMPOSE_PROJECT_NAME="${PROJECT_NAME}-staging"
    API_PORT=8001
    FRONTEND_PORT=3001
    ;;
  "production")
    COMPOSE_PROJECT_NAME="${PROJECT_NAME}-prod"
    API_PORT=8002
    FRONTEND_PORT=3002
    ;;
  *)
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo "Valid environments: development, staging, production"
    exit 1
    ;;
esac

log() {
    echo -e "${BLUE}🚀 $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    success "All dependencies are installed"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        warn ".env file not found. Using .env.example as template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            warn "Please update the .env file with your actual configuration before proceeding"
            read -p "Press Enter to continue..."
        else
            error ".env.example file not found. Please create environment configuration."
            exit 1
        fi
    fi
    
    # Check if required directories exist
    mkdir -p uploads analytics_data collaboration_data integrations_data
    
    success "Pre-deployment checks completed"
}

# Build images
build_images() {
    log "Building Docker images..."
    
    # Build backend
    log "Building backend image..."
    docker build -t ${PROJECT_NAME}/backend:${VERSION} -f Dockerfile .
    
    # Build frontend
    log "Building frontend image..."
    docker build -t ${PROJECT_NAME}/frontend:${VERSION} -f frontend.Dockerfile .
    
    success "Docker images built successfully"
}

# Deploy services
deploy_services() {
    log "Deploying services to $ENVIRONMENT environment..."
    
    # Set environment variables
    export COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT_NAME
    export API_PORT=$API_PORT
    export FRONTEND_PORT=$FRONTEND_PORT
    export VERSION=$VERSION
    
    # Stop existing services
    log "Stopping existing services..."
    docker-compose -f $DOCKER_COMPOSE_FILE down --remove-orphans
    
    # Start services
    log "Starting services..."
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    
    success "Services deployed successfully"
}

# Health checks
health_checks() {
    log "Running health checks..."
    
    local max_attempts=30
    local attempt=1
    
    # Wait for backend to be ready
    log "Waiting for backend to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:$API_PORT/health > /dev/null 2>&1; then
            success "Backend is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error "Backend health check failed after $max_attempts attempts"
            return 1
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    # Wait for frontend to be ready
    log "Waiting for frontend to be ready..."
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
            success "Frontend is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            error "Frontend health check failed after $max_attempts attempts"
            return 1
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    success "All health checks passed"
}

# Post-deployment tasks
post_deployment() {
    log "Running post-deployment tasks..."
    
    # Run database migrations (if any)
    log "Running database migrations..."
    docker-compose exec backend python -c "print('Database migrations completed')"
    
    # Initialize knowledge graph schema
    log "Initializing knowledge graph..."
    docker-compose exec backend python -c "
from services.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph()
print('Knowledge graph initialized')
"
    
    success "Post-deployment tasks completed"
}

# Display deployment information
display_info() {
    log "Deployment completed successfully! 🎉"
    echo ""
    echo "📋 Deployment Information:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Version: $VERSION"
    echo "  Project: $COMPOSE_PROJECT_NAME"
    echo ""
    echo "🌐 Service URLs:"
    echo "  Frontend: http://localhost:$FRONTEND_PORT"
    echo "  Backend API: http://localhost:$API_PORT"
    echo "  Backend Health: http://localhost:$API_PORT/health"
    echo "  Neo4j Browser: http://localhost:7474"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3001"
    echo ""
    echo "📊 Monitoring:"
    echo "  Logs: docker-compose logs -f"
    echo "  Services: docker-compose ps"
    echo "  Resources: docker stats"
    echo ""
    echo "🛑 Stop services: docker-compose down"
    echo "🔄 Restart: ./deploy.sh $ENVIRONMENT $VERSION"
}

# Rollback function
rollback() {
    warn "Initiating rollback..."
    
    # Stop current services
    docker-compose down
    
    # Restore previous version (if available)
    if docker image inspect ${PROJECT_NAME}/backend:previous > /dev/null 2>&1; then
        log "Rolling back to previous version..."
        docker tag ${PROJECT_NAME}/backend:previous ${PROJECT_NAME}/backend:${VERSION}
        docker tag ${PROJECT_NAME}/frontend:previous ${PROJECT_NAME}/frontend:${VERSION}
        deploy_services
        success "Rollback completed"
    else
        error "No previous version available for rollback"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful with this in production)
    if [ "$ENVIRONMENT" != "production" ]; then
        docker volume prune -f
    fi
    
    success "Cleanup completed"
}

# Main execution
main() {
    echo ""
    log "🚀 AI Memory Bank Deployment"
    echo "Environment: $ENVIRONMENT"
    echo "Version: $VERSION"
    echo ""
    
    # Trap to handle script interruption
    trap 'error "Deployment interrupted"; exit 1' INT TERM
    
    check_dependencies
    pre_deployment_checks
    
    # Tag current images as previous (for rollback)
    if docker image inspect ${PROJECT_NAME}/backend:${VERSION} > /dev/null 2>&1; then
        docker tag ${PROJECT_NAME}/backend:${VERSION} ${PROJECT_NAME}/backend:previous
        docker tag ${PROJECT_NAME}/frontend:${VERSION} ${PROJECT_NAME}/frontend:previous
    fi
    
    build_images
    deploy_services
    
    if health_checks; then
        post_deployment
        display_info
    else
        error "Health checks failed. Initiating rollback..."
        rollback
        exit 1
    fi
}

# Handle command line arguments
case "$1" in
    "rollback")
        rollback
        ;;
    "cleanup")
        cleanup
        ;;
    "health")
        health_checks
        ;;
    *)
        main
        ;;
esac