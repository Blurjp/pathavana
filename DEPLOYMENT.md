# Pathavana Deployment Guide

This guide covers the deployment of the Pathavana travel planning application across different environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Development Deployment](#development-deployment)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [Monitoring and Logging](#monitoring-and-logging)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker** (v20.0+) and **Docker Compose** (v2.0+)
- **Kubernetes** (v1.25+) and **kubectl**
- **Terraform** (v1.0+)
- **Helm** (v3.0+)
- **AWS CLI** (v2.0+) or cloud provider CLI
- **Node.js** (v18+) and **npm**
- **Python** (v3.11+) and **pip**

### Cloud Infrastructure

- AWS account with appropriate permissions
- Domain name with DNS management access
- SSL certificates (Let's Encrypt or commercial)
- Container registry access (ECR, Docker Hub, etc.)

### Secrets and API Keys

Obtain the following before deployment:

- OpenAI API key
- Anthropic API key
- Amadeus Travel API credentials
- Google Maps API key
- SMTP credentials for email
- OAuth provider credentials (Google, Facebook, Microsoft)

## Environment Setup

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-org/pathavana.git
cd pathavana

# Run the setup script
chmod +x scripts/env/setup_env.sh
./scripts/env/setup_env.sh
```

### 2. Environment Configuration

Copy and customize environment files:

```bash
# Main environment file
cp .env.example .env

# Backend environments
cp backend/.env.development backend/.env.local
cp backend/.env.test backend/.env.test.local

# Frontend environments
cp frontend/.env.development frontend/.env.local
```

### 3. Validate Configuration

```bash
# Validate environment variables
python3 scripts/env/validate_env.py --env development

# Test Docker setup
docker-compose config
```

## Development Deployment

### 1. Local Development with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 2. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database Admin**: http://localhost:5050 (pgAdmin)
- **Redis Admin**: http://localhost:8001 (RedisInsight)

### 3. Development Commands

```bash
# Database migrations
docker-compose exec backend alembic upgrade head

# Seed test data
docker-compose exec backend python scripts/seed_data.py

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm test

# Restart specific service
docker-compose restart backend
```

### 4. Hot Reload Development

For active development with hot reload:

```bash
# Start infrastructure only
docker-compose up -d postgres redis

# Run backend locally
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend locally (in another terminal)
cd frontend
npm install
npm start
```

## Staging Deployment

### 1. Infrastructure Setup with Terraform

```bash
cd terraform/environments/staging

# Initialize Terraform
terraform init

# Review and customize variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with staging values

# Plan deployment
terraform plan

# Apply infrastructure
terraform apply
```

### 2. Kubernetes Deployment

```bash
# Configure kubectl for staging cluster
aws eks update-kubeconfig --region us-east-1 --name pathavana-staging-cluster

# Deploy using Kustomize
kubectl apply -k k8s/staging/

# Check deployment status
kubectl get pods -n pathavana-staging
kubectl get services -n pathavana-staging
kubectl get ingress -n pathavana-staging
```

### 3. Secrets Management

```bash
# Create sealed secrets
echo -n "your-secret-value" | kubeseal --raw --from-file=/dev/stdin --name pathavana-secrets --namespace pathavana-staging

# Apply secrets
kubectl apply -f security/secrets/staging-sealed-secrets.yaml

# Verify secrets
kubectl get secrets -n pathavana-staging
```

### 4. Database Setup

```bash
# Run migrations
kubectl exec -it deployment/pathavana-backend -n pathavana-staging -- alembic upgrade head

# Seed staging data
kubectl exec -it deployment/pathavana-backend -n pathavana-staging -- python scripts/seed_data.py --env staging
```

## Production Deployment

### 1. Pre-deployment Checklist

- [ ] All secrets properly configured and encrypted
- [ ] SSL certificates installed and valid
- [ ] DNS records configured
- [ ] Monitoring and alerting setup
- [ ] Backup procedures tested
- [ ] Security scanning completed
- [ ] Performance testing passed
- [ ] Disaster recovery plan documented

### 2. Infrastructure Deployment

```bash
cd terraform/environments/prod

# Validate production configuration
terraform validate
terraform plan

# Deploy infrastructure (requires approval)
terraform apply

# Verify infrastructure
aws eks describe-cluster --name pathavana-prod-cluster
```

### 3. Blue-Green Deployment

```bash
# Configure kubectl for production
aws eks update-kubeconfig --region us-east-1 --name pathavana-prod-cluster

# Deploy to green environment
kubectl apply -k k8s/production/

# Verify green deployment
kubectl get pods -n pathavana-production -l version=green

# Run health checks
kubectl exec -it deployment/pathavana-backend-green -n pathavana-production -- curl http://localhost:8000/health

# Switch traffic (blue-green swap)
kubectl patch service pathavana-backend -p '{"spec":{"selector":{"version":"green"}}}' -n pathavana-production
kubectl patch service pathavana-frontend -p '{"spec":{"selector":{"version":"green"}}}' -n pathavana-production

# Verify production traffic
curl -f https://pathavana.com/health
```

### 4. Database Migration (Production)

```bash
# Create database backup before migration
kubectl create job backup-pre-migration --from=cronjob/database-backup -n pathavana-production

# Wait for backup completion
kubectl wait --for=condition=complete job/backup-pre-migration -n pathavana-production --timeout=600s

# Run migrations
kubectl exec -it deployment/pathavana-backend-green -n pathavana-production -- alembic upgrade head

# Verify migration
kubectl exec -it deployment/pathavana-backend-green -n pathavana-production -- python scripts/verify_migrations.py
```

### 5. Post-deployment Verification

```bash
# Health checks
curl -f https://pathavana.com/health
curl -f https://pathavana.com/api/v1/health

# Performance verification
curl -w "@curl-format.txt" -o /dev/null -s https://pathavana.com/

# Monitoring verification
kubectl get pods -n monitoring
curl -f https://grafana.pathavana.com/api/health
```

## CI/CD Pipeline Deployment

### 1. GitHub Actions Setup

The repository includes automated CI/CD pipelines:

- **CI Pipeline** (`.github/workflows/ci.yml`): Runs on PRs and pushes
- **Deployment Pipeline** (`.github/workflows/deploy.yml`): Deploys to staging/production
- **Security Scanning** (`.github/workflows/security-scan.yml`): Continuous security monitoring

### 2. Required Secrets

Configure these secrets in GitHub repository settings:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
KUBECONFIG_STAGING
KUBECONFIG_PRODUCTION
DOCKER_REGISTRY_TOKEN
SLACK_WEBHOOK_URL
SNYK_TOKEN
```

### 3. Deployment Triggers

- **Staging**: Automatic deployment on merge to `main` branch
- **Production**: Manual trigger or Git tags (`v*`)

```bash
# Create production release
git tag v1.0.0
git push origin v1.0.0
```

## Monitoring and Logging

### 1. Monitoring Stack

Access monitoring services:

- **Grafana**: https://grafana.pathavana.com
- **Prometheus**: https://prometheus.pathavana.com
- **AlertManager**: https://alerts.pathavana.com

### 2. Key Metrics to Monitor

- Application response times (95th percentile < 2s)
- Error rates (< 1% for 5xx errors)
- Database connection pool usage (< 80%)
- Redis memory usage (< 90%)
- CPU usage (< 80%)
- Memory usage (< 85%)

### 3. Log Aggregation

```bash
# View application logs
kubectl logs -f deployment/pathavana-backend -n pathavana-production

# Access centralized logs
# Kibana: https://logs.pathavana.com
# Loki/Grafana: https://grafana.pathavana.com
```

### 4. Alerting

Critical alerts are sent to:
- Slack channel: #pathavana-alerts
- PagerDuty for production issues
- Email for non-critical warnings

## Security Considerations

### 1. Network Security

- All traffic encrypted in transit (TLS 1.2+)
- Network policies implemented for pod-to-pod communication
- WAF protection for web applications
- VPC security groups limiting access

### 2. Secret Management

- Sealed Secrets for Kubernetes secrets
- AWS Secrets Manager for external secrets
- Regular secret rotation (90 days for database, 180 days for API keys)
- No secrets in Git repositories

### 3. Container Security

- Base images scanned for vulnerabilities
- Non-root container execution
- Read-only root filesystems where possible
- Minimal container attack surface

### 4. Access Control

- RBAC policies for Kubernetes access
- MFA required for production access
- Least privilege principle
- Regular access reviews

## Backup and Disaster Recovery

### 1. Database Backups

Automated backups run daily:

```bash
# Manual backup
kubectl create job manual-backup-$(date +%Y%m%d) --from=cronjob/database-backup -n pathavana-production

# Restore from backup
kubectl exec -it deployment/postgres -n pathavana-production -- pg_restore -d pathavana /backups/backup-20240101.sql
```

### 2. Disaster Recovery

**RTO (Recovery Time Objective)**: 4 hours
**RPO (Recovery Point Objective)**: 1 hour

Recovery procedures:
1. Activate backup infrastructure in secondary region
2. Restore database from latest backup
3. Update DNS to point to backup region
4. Verify application functionality

## Performance Optimization

### 1. Scaling Configuration

```yaml
# Horizontal Pod Autoscaler
minReplicas: 2
maxReplicas: 10
targetCPUUtilizationPercentage: 70
targetMemoryUtilizationPercentage: 80
```

### 2. Database Optimization

- Connection pooling configured
- Query optimization monitoring
- Read replicas for read-heavy workloads
- Database query caching

### 3. CDN Configuration

Static assets served via CloudFront:
- Global edge locations
- Automatic compression
- Cache invalidation on deployments

## Cost Optimization

### 1. Resource Right-sizing

- Regular review of resource requests/limits
- Spot instances for non-critical workloads
- Auto-scaling based on demand
- Reserved instances for predictable workloads

### 2. Monitoring Costs

- AWS Cost Explorer integration
- Budget alerts set up
- Resource tagging for cost allocation
- Monthly cost reviews

Estimated monthly costs:
- **Development**: $100-200
- **Staging**: $200-400
- **Production**: $500-1000

## Troubleshooting

### Common Issues

#### 1. Pod Startup Issues

```bash
# Check pod status
kubectl get pods -n pathavana-production

# View pod logs
kubectl logs deployment/pathavana-backend -n pathavana-production

# Describe pod for events
kubectl describe pod <pod-name> -n pathavana-production
```

#### 2. Database Connection Issues

```bash
# Test database connectivity
kubectl exec -it deployment/pathavana-backend -n pathavana-production -- python -c "
import asyncpg
import asyncio
async def test_db():
    conn = await asyncpg.connect('postgresql://...')
    result = await conn.fetchval('SELECT 1')
    print(f'Database test: {result}')
asyncio.run(test_db())
"
```

#### 3. Performance Issues

```bash
# Check resource usage
kubectl top pods -n pathavana-production
kubectl top nodes

# Scale deployment if needed
kubectl scale deployment pathavana-backend --replicas=5 -n pathavana-production
```

#### 4. SSL Certificate Issues

```bash
# Check certificate status
kubectl describe certificate tls-secret -n pathavana-production

# Force certificate renewal
kubectl delete certificate tls-secret -n pathavana-production
kubectl apply -f k8s/production/
```

### Emergency Procedures

#### 1. Production Incident Response

1. **Immediate Response** (< 5 minutes)
   - Check application health dashboard
   - Review recent deployments
   - Check infrastructure alerts

2. **Investigation** (< 15 minutes)
   - Review application and infrastructure logs
   - Check database and Redis status
   - Verify external service dependencies

3. **Resolution** (< 30 minutes)
   - Implement fix or rollback
   - Verify resolution
   - Document incident

#### 2. Rollback Procedures

```bash
# Quick rollback to previous version
kubectl rollout undo deployment/pathavana-backend -n pathavana-production
kubectl rollout undo deployment/pathavana-frontend -n pathavana-production

# Rollback to specific revision
kubectl rollout history deployment/pathavana-backend -n pathavana-production
kubectl rollout undo deployment/pathavana-backend --to-revision=2 -n pathavana-production
```

### Contact Information

**Development Team**: dev-team@pathavana.com
**DevOps Team**: devops@pathavana.com
**Security Team**: security@pathavana.com
**On-call Engineer**: +1-XXX-XXX-XXXX

**Escalation Matrix**:
1. Development Team Lead
2. Engineering Manager
3. CTO
4. CEO (for business-critical incidents)

---

For additional support, please refer to:
- [Infrastructure Documentation](INFRASTRUCTURE.md)
- [Monitoring Documentation](MONITORING.md)
- [Security Documentation](SECURITY.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)