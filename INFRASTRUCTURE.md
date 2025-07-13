# Pathavana Infrastructure Overview

This document provides a comprehensive overview of the Pathavana infrastructure architecture, components, and operational procedures.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Infrastructure Components](#infrastructure-components)
- [Network Architecture](#network-architecture)
- [Security Architecture](#security-architecture)
- [Data Architecture](#data-architecture)
- [Monitoring and Observability](#monitoring-and-observability)
- [Disaster Recovery](#disaster-recovery)
- [Cost Management](#cost-management)
- [Maintenance Procedures](#maintenance-procedures)

## Architecture Overview

Pathavana uses a modern, cloud-native architecture built on Kubernetes with the following principles:

- **Microservices Architecture**: Loosely coupled services
- **Containerization**: Docker containers for consistent deployments
- **Infrastructure as Code**: Terraform for infrastructure management
- **GitOps**: Git-based deployment workflows
- **Observability**: Comprehensive monitoring and logging
- **Security**: Defense in depth with multiple security layers

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Internet/CDN                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                  Load Balancer (ALB)                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                 Kubernetes Cluster                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Frontend   │  │   Backend   │  │  Monitoring │             │
│  │   (React)   │  │ (FastAPI)   │  │   Stack     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                          │                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ PostgreSQL  │  │    Redis    │  │   Backup    │             │
│  │ (Database)  │  │   (Cache)   │  │   Service   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│               External Services                                  │
│  OpenAI API │ Amadeus API │ Google Maps │ SMTP Service          │
└─────────────────────────────────────────────────────────────────┘
```

## Infrastructure Components

### 1. Compute Infrastructure

#### Amazon EKS Cluster
- **Version**: Kubernetes 1.28
- **Node Groups**:
  - **On-Demand**: 2-10 t3.medium instances
  - **Spot**: 0-5 t3.medium instances (development/testing)
- **Auto Scaling**: Horizontal Pod Autoscaler (HPA) and Cluster Autoscaler
- **Availability**: Multi-AZ deployment across 3 availability zones

#### Container Registry
- **Amazon ECR** for Docker image storage
- **Image Scanning**: Automated vulnerability scanning on push
- **Lifecycle Policies**: Automatic cleanup of old images

### 2. Storage Infrastructure

#### Database (Amazon RDS)
- **Engine**: PostgreSQL 15.4
- **Instance Class**: 
  - Development: db.t3.micro
  - Staging: db.t3.small
  - Production: db.t3.medium
- **Storage**: 20GB initial, auto-scaling up to 100GB
- **Backup**: Automated daily backups with 7-day retention
- **Multi-AZ**: Enabled for production
- **Encryption**: At-rest encryption enabled

#### Cache (Amazon ElastiCache)
- **Engine**: Redis 7.0
- **Node Type**:
  - Development: cache.t3.micro
  - Staging: cache.t3.small
  - Production: cache.t3.medium
- **Replication**: Single node (development), Multi-AZ (production)
- **Backup**: Automated snapshots

#### Object Storage (Amazon S3)
- **Buckets**:
  - `pathavana-{env}-assets`: Static assets and uploads
  - `pathavana-{env}-backups`: Database backups
  - `pathavana-{env}-logs`: Log archives
- **Versioning**: Enabled with lifecycle policies
- **Encryption**: AES-256 server-side encryption

### 3. Networking Infrastructure

#### VPC Configuration
- **CIDR Block**: 10.0.0.0/16
- **Subnets**:
  - Public: 10.0.10.0/24, 10.0.11.0/24, 10.0.12.0/24
  - Private: 10.0.0.0/24, 10.0.1.0/24, 10.0.2.0/24
- **Availability Zones**: us-east-1a, us-east-1b, us-east-1c

#### Load Balancing
- **Application Load Balancer (ALB)**:
  - SSL termination
  - Health checks
  - Path-based routing
  - Rate limiting
- **Network Load Balancer**: For internal services (if needed)

#### CDN (CloudFront)
- **Global Distribution**: 200+ edge locations
- **Caching**: Static assets cached for 1 year
- **Compression**: Automatic gzip compression
- **Security**: AWS WAF integration

### 4. DNS and SSL

#### DNS (Route 53)
- **Hosted Zone**: pathavana.com
- **Records**:
  - A: pathavana.com → ALB
  - CNAME: www.pathavana.com → pathavana.com
  - CNAME: staging.pathavana.com → staging ALB
- **Health Checks**: Automated failover capabilities

#### SSL Certificates
- **Provider**: AWS Certificate Manager (ACM)
- **Validation**: DNS validation
- **Auto-Renewal**: Automatic certificate renewal
- **Cipher Suites**: TLS 1.2+ only

## Network Architecture

### Network Security Layers

1. **Internet Gateway**: Controls internet access
2. **NAT Gateways**: Outbound internet access for private subnets
3. **Security Groups**: Instance-level firewalls
4. **Network ACLs**: Subnet-level access control
5. **Kubernetes Network Policies**: Pod-to-pod communication control

### Traffic Flow

```
Internet → CloudFront → ALB → Ingress Controller → Services → Pods
```

#### Ingress Configuration
- **Controller**: NGINX Ingress Controller
- **SSL**: Automatic HTTPS redirect
- **Rate Limiting**: 100 requests/minute per IP
- **CORS**: Configured for frontend domains

### Service Mesh (Future)
- **Istio**: Planned for service-to-service communication
- **mTLS**: Mutual TLS between services
- **Traffic Management**: Canary deployments, circuit breakers

## Security Architecture

### Defense in Depth Strategy

#### 1. Network Security
- **VPC Isolation**: Private subnets for application components
- **Security Groups**: Least privilege access rules
- **Network Policies**: Kubernetes network segmentation
- **WAF**: Web Application Firewall for common attacks

#### 2. Identity and Access Management
- **AWS IAM**: Role-based access control
- **Kubernetes RBAC**: Fine-grained permissions
- **Service Accounts**: Minimal privileges for applications
- **MFA**: Required for production access

#### 3. Secrets Management
- **AWS Secrets Manager**: Database credentials and API keys
- **Sealed Secrets**: Kubernetes secrets encryption
- **Secret Rotation**: Automated rotation policies
- **Audit Logging**: All secret access logged

#### 4. Container Security
- **Image Scanning**: Vulnerability scanning in CI/CD
- **Runtime Security**: Non-root containers
- **Pod Security Standards**: Restricted security policies
- **Admission Controllers**: Policy enforcement

#### 5. Data Protection
- **Encryption at Rest**: All storage encrypted
- **Encryption in Transit**: TLS for all communication
- **Data Classification**: PII handling procedures
- **Backup Encryption**: Encrypted backups

### Compliance Framework

#### SOC 2 Type II Compliance
- **Security**: Access controls and monitoring
- **Availability**: Uptime and performance monitoring
- **Processing Integrity**: Data validation and error handling
- **Confidentiality**: Data protection measures
- **Privacy**: PII handling procedures

#### GDPR Compliance
- **Data Minimization**: Collect only necessary data
- **Right to Deletion**: Data deletion procedures
- **Data Portability**: Export capabilities
- **Consent Management**: User consent tracking
- **Breach Notification**: Incident response procedures

## Data Architecture

### Data Flow

```
User Input → Frontend → Backend API → Database
                    ↓
              External APIs ← Backend
                    ↓
                  Cache ← Redis
```

### Database Schema

#### Core Tables
- **users**: User accounts and authentication
- **travelers**: Traveler profiles and preferences
- **bookings**: Flight and hotel reservations
- **sessions**: User sessions and chat history
- **audit_logs**: Security and compliance logging

#### Data Retention Policies
- **User Data**: Retained until account deletion
- **Session Data**: 90 days
- **Logs**: 12 months
- **Backups**: 30 days (daily), 12 months (monthly)

### Data Privacy

#### PII Handling
- **Encryption**: All PII encrypted at application level
- **Access Logging**: All PII access logged
- **Data Masking**: Production data masked in non-prod environments
- **Anonymization**: Analytics data anonymized

#### Data Processing
- **Purpose Limitation**: Data used only for stated purposes
- **Storage Limitation**: Automatic data expiration
- **Accuracy**: Data validation and correction procedures
- **Accountability**: Data processing records maintained

## Monitoring and Observability

### Metrics Collection

#### Application Metrics
- **Custom Metrics**: Business logic metrics
- **Performance Metrics**: Response times, throughput
- **Error Metrics**: Error rates and types
- **User Metrics**: Active users, sessions

#### Infrastructure Metrics
- **Resource Usage**: CPU, memory, disk, network
- **Kubernetes Metrics**: Pod status, node health
- **Database Metrics**: Connections, query performance
- **Cache Metrics**: Hit rates, memory usage

### Logging Strategy

#### Log Levels
- **ERROR**: Application errors requiring attention
- **WARN**: Potential issues and degraded performance
- **INFO**: Normal application flow
- **DEBUG**: Detailed debugging information (non-production)

#### Log Aggregation
- **Collection**: Fluentd for log shipping
- **Storage**: Elasticsearch for log storage
- **Analysis**: Kibana for log analysis
- **Retention**: 30 days for detailed logs, 12 months for aggregated logs

### Distributed Tracing

#### Jaeger Integration
- **Trace Collection**: All service interactions traced
- **Performance Analysis**: Identify bottlenecks
- **Error Tracking**: Trace error propagation
- **Service Map**: Visualize service dependencies

### Alerting Framework

#### Alert Categories
- **P0 (Critical)**: Service down, data loss
- **P1 (High)**: Performance degradation, high error rates
- **P2 (Medium)**: Resource constraints, warnings
- **P3 (Low)**: Informational, maintenance reminders

#### Notification Channels
- **Slack**: Real-time alerts for development team
- **PagerDuty**: On-call escalation for critical issues
- **Email**: Non-urgent notifications
- **SMS**: Critical production alerts

## Disaster Recovery

### Business Continuity Plan

#### Recovery Objectives
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour
- **MTTR (Mean Time to Recovery)**: 2 hours
- **Availability Target**: 99.9% uptime

### Backup Strategy

#### Database Backups
- **Frequency**: Daily automated backups
- **Retention**: 7 days point-in-time recovery
- **Cross-Region**: Weekly backups to secondary region
- **Testing**: Monthly backup restoration tests

#### Application Backups
- **Infrastructure**: Terraform state backed up
- **Configuration**: Git repository serves as backup
- **Secrets**: AWS Secrets Manager automatic backup
- **Container Images**: ECR cross-region replication

### Multi-Region Setup

#### Primary Region: us-east-1
- **Production Environment**: Full deployment
- **Database**: Primary RDS instance
- **Monitoring**: Complete monitoring stack

#### Secondary Region: us-west-2
- **Disaster Recovery**: Standby infrastructure
- **Database**: Read replica and backup restoration capability
- **Monitoring**: Basic health monitoring

### Failover Procedures

#### Automatic Failover
1. **Health Check Failure**: Route 53 health checks detect failure
2. **DNS Failover**: Traffic routed to secondary region
3. **Database Promotion**: Read replica promoted to primary
4. **Application Scaling**: Auto-scaling activates standby resources

#### Manual Failover
1. **Assessment**: Evaluate primary region status
2. **Decision**: Go/no-go decision for failover
3. **Communication**: Notify stakeholders
4. **Execution**: Follow documented runbook
5. **Verification**: Confirm secondary region functionality

## Cost Management

### Cost Optimization Strategies

#### Resource Optimization
- **Right-Sizing**: Regular review of instance sizes
- **Auto-Scaling**: Scale resources based on demand
- **Spot Instances**: Use for non-critical workloads
- **Reserved Instances**: Commit to long-term capacity

#### Storage Optimization
- **Lifecycle Policies**: Automatic data archival
- **Compression**: Reduce storage requirements
- **Deduplication**: Eliminate redundant data
- **Intelligent Tiering**: Automatic storage class optimization

### Cost Monitoring

#### Budget Alerts
- **Monthly Budget**: $1000 for production environment
- **Alert Thresholds**: 50%, 80%, 100% of budget
- **Forecasting**: Projected cost based on current usage
- **Cost Anomaly Detection**: Unusual spending patterns

#### Cost Allocation
- **Tagging Strategy**: Consistent resource tagging
- **Cost Centers**: Engineering, Operations, Security
- **Project Tracking**: Feature development costs
- **Chargeback**: Department cost allocation

### Estimated Monthly Costs

#### Production Environment
- **EKS Cluster**: $73/month
- **Worker Nodes**: $150/month (3 x t3.medium)
- **RDS PostgreSQL**: $45/month (db.t3.medium)
- **ElastiCache Redis**: $35/month (cache.t3.medium)
- **Load Balancer**: $16/month
- **NAT Gateway**: $32/month
- **Data Transfer**: $50/month (estimated)
- **Storage**: $30/month
- **Total**: ~$431/month

#### Staging Environment
- **Total**: ~$200/month (50% of production)

#### Development Environment
- **Total**: ~$100/month (local development + shared staging resources)

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily
- [ ] Check application health dashboards
- [ ] Review error logs and alerts
- [ ] Monitor resource utilization
- [ ] Verify backup completion

#### Weekly
- [ ] Review performance metrics
- [ ] Update security patches
- [ ] Test backup restoration
- [ ] Review cost reports

#### Monthly
- [ ] Update Kubernetes version (if available)
- [ ] Review and rotate secrets
- [ ] Conduct disaster recovery test
- [ ] Review access permissions
- [ ] Update documentation

#### Quarterly
- [ ] Security audit and penetration testing
- [ ] Review and update disaster recovery plan
- [ ] Capacity planning review
- [ ] Cost optimization review
- [ ] Update compliance documentation

### Upgrade Procedures

#### Kubernetes Upgrades
1. **Planning**: Review upgrade path and breaking changes
2. **Testing**: Test upgrade in development environment
3. **Staging**: Upgrade staging environment first
4. **Backup**: Create cluster backup before upgrade
5. **Production**: Perform rolling upgrade during maintenance window
6. **Verification**: Verify all services after upgrade

#### Application Upgrades
1. **Code Review**: Peer review of all changes
2. **Testing**: Automated and manual testing
3. **Security Scan**: Security vulnerability scanning
4. **Staging Deployment**: Deploy to staging first
5. **Production Deployment**: Blue-green deployment strategy
6. **Rollback Plan**: Prepared rollback procedures

### Emergency Procedures

#### Incident Response
1. **Detection**: Automated alerts or manual detection
2. **Assessment**: Evaluate impact and severity
3. **Response**: Immediate mitigation steps
4. **Communication**: Notify stakeholders
5. **Resolution**: Implement permanent fix
6. **Post-Mortem**: Document lessons learned

#### Contact Information
- **Primary On-Call**: +1-XXX-XXX-XXXX
- **Secondary On-Call**: +1-XXX-XXX-XXXX
- **Engineering Manager**: engineering-manager@pathavana.com
- **DevOps Team**: devops@pathavana.com
- **Security Team**: security@pathavana.com

---

This infrastructure documentation is maintained by the DevOps team and updated quarterly or after significant changes. For questions or clarifications, please contact devops@pathavana.com.