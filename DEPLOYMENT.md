# 🚀 AI Memory Bank - Production Deployment Guide

This comprehensive guide covers deploying the AI Memory Bank application in production environments using Docker, Kubernetes, and various cloud platforms.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Platform Deployment](#cloud-platform-deployment)
6. [Monitoring & Logging](#monitoring--logging)
7. [Security Considerations](#security-considerations)
8. [Performance Optimization](#performance-optimization)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100Mbps

**Recommended for Production:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 200GB+ SSD
- Network: 1Gbps+

### Required Software

- Docker 24.0+
- Docker Compose 2.20+
- Kubernetes 1.28+ (for K8s deployment)
- kubectl (for K8s deployment)
- Helm 3.12+ (optional, for K8s charts)

### External Services

- Supabase project with PgVector enabled
- OpenAI API key
- Hugging Face API token
- SSL certificates (for HTTPS)

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ai-memory-bank.git
cd ai-memory-bank
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file with your production values:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:secure_password@postgres:5432/ai_memory_bank
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secure_neo4j_password
REDIS_URL=redis://redis:6379

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key

# API Keys
OPENAI_API_KEY=your-openai-api-key
HUGGINGFACE_API_TOKEN=your-huggingface-token

# Security
SECRET_KEY=your-super-secret-jwt-key-min-32-characters
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Production Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 3. SSL Certificate Setup

For HTTPS, place your SSL certificates in the `nginx/ssl/` directory:

```bash
mkdir -p nginx/ssl
# Copy your certificates
cp your-cert.pem nginx/ssl/cert.pem
cp your-private-key.pem nginx/ssl/key.pem
```

## Docker Deployment

### Quick Start

```bash
# Make deployment script executable
chmod +x scripts/deployment/deploy.sh

# Deploy to production
./scripts/deployment/deploy.sh production latest
```

### Manual Deployment

1. **Build Images**:
```bash
# Build backend image
docker build -t ai-memory-bank/backend:latest -f Dockerfile .

# Build frontend image  
docker build -t ai-memory-bank/frontend:latest -f frontend.Dockerfile .
```

2. **Deploy with Docker Compose**:
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

3. **Health Check**:
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000
```

### Service URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Neo4j Browser: http://localhost:7474
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

## Kubernetes Deployment

### Prerequisites

1. **Kubernetes Cluster**: Ensure you have a running K8s cluster
2. **kubectl**: Configured to connect to your cluster
3. **Storage Classes**: Available for persistent volumes

### Deployment Steps

1. **Create Namespace**:
```bash
kubectl apply -f k8s/deployment.yaml
```

2. **Verify Deployment**:
```bash
# Check pods
kubectl get pods -n ai-memory-bank

# Check services
kubectl get services -n ai-memory-bank

# Check ingress
kubectl get ingress -n ai-memory-bank
```

3. **Access Application**:
```bash
# Port forward for local access
kubectl port-forward -n ai-memory-bank service/frontend 3000:3000
kubectl port-forward -n ai-memory-bank service/backend 8000:8000
```

### Scaling

```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n ai-memory-bank

# Scale frontend
kubectl scale deployment frontend --replicas=3 -n ai-memory-bank
```

## Cloud Platform Deployment

### AWS EKS

1. **Create EKS Cluster**:
```bash
eksctl create cluster --name ai-memory-bank --version 1.28 --region us-west-2 --nodegroup-name standard-workers --node-type t3.medium --nodes 3 --nodes-min 1 --nodes-max 4
```

2. **Deploy Application**:
```bash
kubectl apply -f k8s/deployment.yaml
```

3. **Setup Load Balancer**:
```bash
# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller/crds?ref=master"
```

### Google GKE

1. **Create GKE Cluster**:
```bash
gcloud container clusters create ai-memory-bank \
    --zone=us-central1-a \
    --machine-type=n1-standard-2 \
    --num-nodes=3 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5
```

2. **Deploy Application**:
```bash
kubectl apply -f k8s/deployment.yaml
```

### Azure AKS

1. **Create AKS Cluster**:
```bash
az aks create \
    --resource-group myResourceGroup \
    --name ai-memory-bank \
    --node-count 3 \
    --enable-addons monitoring \
    --generate-ssh-keys
```

2. **Deploy Application**:
```bash
kubectl apply -f k8s/deployment.yaml
```

## Monitoring & Logging

### Prometheus & Grafana

The deployment includes Prometheus and Grafana for monitoring:

1. **Access Prometheus**: http://localhost:9090
2. **Access Grafana**: http://localhost:3001 (admin/admin123)

### Custom Dashboards

Import the provided Grafana dashboards from `monitoring/grafana/dashboards/`:

- **Application Metrics**: API response times, request rates, error rates
- **System Metrics**: CPU, memory, disk usage
- **Database Metrics**: Query performance, connection pools
- **Business Metrics**: User activity, document processing stats

### Log Aggregation

For production, consider implementing centralized logging:

```bash
# Deploy ELK Stack (optional)
kubectl apply -f k8s/logging/elasticsearch.yaml
kubectl apply -f k8s/logging/logstash.yaml
kubectl apply -f k8s/logging/kibana.yaml
```

## Security Considerations

### 1. Network Security

- Use HTTPS/TLS for all communications
- Implement proper firewall rules
- Use VPC/network segmentation
- Enable DDoS protection

### 2. Authentication & Authorization

- Implement JWT-based authentication
- Use strong password policies
- Enable 2FA where possible
- Regular security audits

### 3. Data Protection

- Encrypt data at rest and in transit
- Regular security updates
- Backup encryption
- GDPR compliance measures

### 4. Container Security

```bash
# Scan images for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image ai-memory-bank/backend:latest

# Use non-root users in containers
# Implement resource limits
# Regular base image updates
```

## Performance Optimization

### 1. Database Optimization

**PostgreSQL:**
```sql
-- Optimize connection pooling
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

**Neo4j:**
```
# Increase heap size
NEO4J_dbms_memory_heap_max__size=2g
NEO4J_dbms_memory_pagecache_size=1g
```

### 2. Application Optimization

- Enable Redis caching
- Implement connection pooling
- Use async/await for I/O operations
- Optimize vector similarity searches
- Implement request rate limiting

### 3. Frontend Optimization

- Enable CDN for static assets
- Implement lazy loading
- Optimize bundle sizes
- Use service workers for caching

## Backup & Recovery

### 1. Database Backups

**PostgreSQL:**
```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
docker exec postgres pg_dump -U postgres ai_memory_bank > $BACKUP_DIR/backup_$DATE.sql
```

**Neo4j:**
```bash
# Neo4j backup
docker exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j_$DATE.dump
```

### 2. File System Backups

```bash
# Backup uploaded files and data
rsync -av --delete /path/to/uploads/ /backups/uploads/
rsync -av --delete /path/to/analytics_data/ /backups/analytics/
```

### 3. Recovery Procedures

1. **Database Recovery**:
```bash
# PostgreSQL restore
docker exec -i postgres psql -U postgres -d ai_memory_bank < backup.sql

# Neo4j restore
docker exec neo4j neo4j-admin load --database=neo4j --from=/backups/neo4j.dump
```

2. **Application Recovery**:
```bash
# Restore from backup
./scripts/deployment/deploy.sh production backup-version

# Verify integrity
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

**1. Service Won't Start**
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Check resource usage
docker stats

# Restart specific service
docker-compose restart backend
```

**2. Database Connection Issues**
```bash
# Check database status
docker-compose exec postgres pg_isready

# Check Neo4j
docker-compose exec neo4j cypher-shell -u neo4j -p password123
```

**3. High Memory Usage**
```bash
# Check memory usage
free -h
docker stats

# Optimize services
# Reduce worker processes
# Implement memory limits
```

**4. Slow Performance**
```bash
# Check database queries
# Enable query logging
# Monitor API response times
# Check vector search performance
```

### Health Checks

```bash
# Comprehensive health check
./scripts/deployment/deploy.sh health

# Individual service checks
curl http://localhost:8000/health  # Backend
curl http://localhost:3000         # Frontend
curl http://localhost:7474         # Neo4j
curl http://localhost:9090         # Prometheus
```

### Log Analysis

```bash
# View aggregated logs
docker-compose logs -f --tail=100

# Search for errors
docker-compose logs backend | grep ERROR

# Monitor real-time logs
docker-compose logs -f backend frontend
```

## Maintenance

### Regular Tasks

1. **Weekly**:
   - Check service health
   - Review resource usage
   - Update security patches
   - Verify backups

2. **Monthly**:
   - Performance optimization review
   - Security audit
   - Capacity planning
   - Update dependencies

3. **Quarterly**:
   - Disaster recovery test
   - Security penetration testing
   - Architecture review
   - Cost optimization

### Updates & Migrations

```bash
# Update to new version
git pull origin main
./scripts/deployment/deploy.sh production v2.0.0

# Rollback if needed
./scripts/deployment/deploy.sh rollback
```

### Resource Monitoring

- Set up alerts for high CPU/memory usage
- Monitor disk space usage
- Track API response times
- Monitor error rates

## Support & Documentation

For additional support:
- 📧 Email: support@ai-memory-bank.com
- 📝 Documentation: https://docs.ai-memory-bank.com
- 🐛 Issues: https://github.com/your-org/ai-memory-bank/issues
- 💬 Community: https://discord.gg/ai-memory-bank

---

**🎉 Congratulations! Your AI Memory Bank is now deployed and ready for production use!**