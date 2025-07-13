# Pathavana Troubleshooting Guide

This guide provides step-by-step troubleshooting procedures for common issues in the Pathavana application.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Application Issues](#application-issues)
- [Infrastructure Issues](#infrastructure-issues)
- [Database Issues](#database-issues)
- [Network and Connectivity](#network-and-connectivity)
- [Performance Issues](#performance-issues)
- [Security Issues](#security-issues)
- [Deployment Issues](#deployment-issues)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Emergency Procedures](#emergency-procedures)

## Quick Reference

### Essential Commands

```bash
# Check application status
kubectl get pods -n pathavana-production
kubectl get services -n pathavana-production
kubectl get ingress -n pathavana-production

# View application logs
kubectl logs -f deployment/pathavana-backend -n pathavana-production
kubectl logs -f deployment/pathavana-frontend -n pathavana-production

# Check resource usage
kubectl top pods -n pathavana-production
kubectl top nodes

# Database access
kubectl exec -it deployment/postgres -n pathavana-production -- psql -U postgres -d pathavana

# Cache access
kubectl exec -it deployment/redis -n pathavana-production -- redis-cli
```

### Health Check URLs

- **Frontend**: https://pathavana.com/health
- **Backend API**: https://pathavana.com/api/v1/health
- **Database**: Internal health check via backend
- **Cache**: Internal health check via backend

### Contact Information

- **On-call Engineer**: +1-XXX-XXX-XXXX
- **DevOps Team**: devops@pathavana.com
- **Slack**: #pathavana-alerts
- **PagerDuty**: pathavana.pagerduty.com

## Application Issues

### Backend API Not Responding

#### Symptoms
- HTTP 502/503 errors
- API requests timing out
- Health check failures

#### Diagnosis Steps

1. **Check Pod Status**
   ```bash
   kubectl get pods -n pathavana-production -l component=backend
   kubectl describe pod <pod-name> -n pathavana-production
   ```

2. **Check Application Logs**
   ```bash
   kubectl logs -f deployment/pathavana-backend -n pathavana-production --tail=100
   ```

3. **Check Resource Usage**
   ```bash
   kubectl top pods -n pathavana-production -l component=backend
   ```

4. **Test Database Connectivity**
   ```bash
   kubectl exec -it deployment/pathavana-backend -n pathavana-production -- python -c "
   import asyncpg
   import asyncio
   async def test():
       conn = await asyncpg.connect('$DATABASE_URL')
       result = await conn.fetchval('SELECT 1')
       print(f'DB test: {result}')
   asyncio.run(test())
   "
   ```

#### Common Solutions

**Pod Crashes/Restarts**
```bash
# Check recent events
kubectl get events -n pathavana-production --sort-by='.lastTimestamp'

# Restart deployment
kubectl rollout restart deployment/pathavana-backend -n pathavana-production
```

**Memory Issues**
```bash
# Increase memory limits
kubectl patch deployment pathavana-backend -n pathavana-production -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "backend",
          "resources": {
            "limits": {"memory": "2Gi"},
            "requests": {"memory": "1Gi"}
          }
        }]
      }
    }
  }
}'
```

**Database Connection Issues**
```bash
# Check database pod status
kubectl get pods -n pathavana-production -l component=postgres

# Test database connectivity
kubectl exec -it deployment/postgres -n pathavana-production -- pg_isready
```

### Frontend Not Loading

#### Symptoms
- Blank page or loading screen
- JavaScript errors in browser console
- Static assets not loading

#### Diagnosis Steps

1. **Check Frontend Pod Status**
   ```bash
   kubectl get pods -n pathavana-production -l component=frontend
   kubectl logs -f deployment/pathavana-frontend -n pathavana-production
   ```

2. **Check Browser Console**
   - Open browser developer tools
   - Look for JavaScript errors
   - Check network tab for failed requests

3. **Test Backend Connectivity**
   ```bash
   # From browser console
   fetch('/api/v1/health').then(r => r.json()).then(console.log)
   ```

#### Common Solutions

**Static Assets Not Loading**
```bash
# Check nginx configuration
kubectl get configmap nginx-config -n pathavana-production -o yaml

# Restart frontend pods
kubectl rollout restart deployment/pathavana-frontend -n pathavana-production
```

**CORS Issues**
```bash
# Check backend CORS configuration
kubectl exec -it deployment/pathavana-backend -n pathavana-production -- env | grep CORS
```

### Authentication Issues

#### Symptoms
- Users cannot log in
- JWT token validation failures
- Session persistence issues

#### Diagnosis Steps

1. **Check Authentication Logs**
   ```bash
   kubectl logs -f deployment/pathavana-backend -n pathavana-production | grep -i auth
   ```

2. **Test JWT Token Generation**
   ```bash
   kubectl exec -it deployment/pathavana-backend -n pathavana-production -- python -c "
   from app.core.security import create_access_token
   token = create_access_token(data={'sub': 'test@example.com'})
   print(f'Test token: {token}')
   "
   ```

3. **Check External OAuth Providers**
   ```bash
   # Test Google OAuth endpoint
   curl -I https://accounts.google.com/.well-known/openid_configuration
   ```

#### Common Solutions

**Secret Key Issues**
```bash
# Verify secret key is set
kubectl get secret pathavana-secrets -n pathavana-production -o jsonpath='{.data.SECRET_KEY}' | base64 -d | wc -c
```

**OAuth Configuration**
```bash
# Check OAuth environment variables
kubectl exec -it deployment/pathavana-backend -n pathavana-production -- env | grep -E "(GOOGLE|FACEBOOK|MICROSOFT)_CLIENT"
```

## Infrastructure Issues

### Kubernetes Cluster Issues

#### Node Not Ready

**Symptoms**
- `kubectl get nodes` shows NotReady status
- Pods stuck in Pending state

**Diagnosis**
```bash
# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check node logs
kubectl logs -n kube-system daemonset/aws-node
```

**Solutions**
```bash
# Restart kubelet on the node
ssh ec2-user@<node-ip>
sudo systemctl restart kubelet

# Drain and uncordon node
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
kubectl uncordon <node-name>
```

#### Pod Stuck in Pending

**Diagnosis**
```bash
kubectl describe pod <pod-name> -n pathavana-production
kubectl get events -n pathavana-production --sort-by='.lastTimestamp'
```

**Common Causes and Solutions**

**Insufficient Resources**
```bash
# Check node capacity
kubectl describe nodes | grep -A 5 "Allocated resources"

# Scale cluster if needed
aws eks update-nodegroup-config --cluster-name pathavana-prod-cluster --nodegroup-name main --scaling-config minSize=3,maxSize=10,desiredSize=5
```

**Image Pull Errors**
```bash
# Check image pull secrets
kubectl get secrets -n pathavana-production | grep registry

# Update image pull secret
kubectl create secret docker-registry registry-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n pathavana-production
```

### Storage Issues

#### Persistent Volume Issues

**Symptoms**
- Database pod fails to start
- Data persistence failures

**Diagnosis**
```bash
# Check PV and PVC status
kubectl get pv,pvc -n pathavana-production
kubectl describe pvc postgres-pvc -n pathavana-production
```

**Solutions**
```bash
# Check storage class
kubectl get storageclass

# Expand PVC if needed
kubectl patch pvc postgres-pvc -n pathavana-production -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'
```

## Database Issues

### Database Connection Failures

#### Symptoms
- Backend cannot connect to database
- Connection timeout errors
- Too many connections error

#### Diagnosis Steps

1. **Check Database Pod Status**
   ```bash
   kubectl get pods -n pathavana-production -l component=postgres
   kubectl logs -f deployment/postgres -n pathavana-production
   ```

2. **Test Database Connectivity**
   ```bash
   kubectl exec -it deployment/postgres -n pathavana-production -- pg_isready -U postgres
   ```

3. **Check Connection Limits**
   ```sql
   SELECT count(*) as current_connections, setting as max_connections 
   FROM pg_stat_activity, pg_settings 
   WHERE name = 'max_connections';
   ```

#### Common Solutions

**Too Many Connections**
```sql
-- Kill idle connections
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND state_change < now() - interval '1 hour';

-- Increase max_connections (requires restart)
ALTER SYSTEM SET max_connections = 200;
SELECT pg_reload_conf();
```

**Connection Pool Issues**
```bash
# Check backend connection pool settings
kubectl exec -it deployment/pathavana-backend -n pathavana-production -- python -c "
from app.core.database import engine
print(f'Pool size: {engine.pool.size()}')
print(f'Checked out: {engine.pool.checkedout()}')
print(f'Overflow: {engine.pool.overflow()}')
"
```

### Database Performance Issues

#### Symptoms
- Slow query performance
- High CPU usage on database
- Lock contention

#### Diagnosis

1. **Check Active Queries**
   ```sql
   SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
   FROM pg_stat_activity 
   WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
   ```

2. **Check Lock Information**
   ```sql
   SELECT 
     blocked_locks.pid AS blocked_pid,
     blocked_activity.usename AS blocked_user,
     blocking_locks.pid AS blocking_pid,
     blocking_activity.usename AS blocking_user,
     blocked_activity.query AS blocked_statement,
     blocking_activity.query AS current_statement_in_blocking_process
   FROM pg_catalog.pg_locks blocked_locks
   JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
   JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
     AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
     AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
     AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
     AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
     AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
     AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
     AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
     AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
     AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
     AND blocking_locks.pid != blocked_locks.pid
   JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
   WHERE NOT blocked_locks.granted;
   ```

3. **Check Query Statistics**
   ```sql
   SELECT query, calls, total_time, mean_time, rows
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   ```

#### Common Solutions

**Long-Running Queries**
```sql
-- Kill long-running query
SELECT pg_terminate_backend(<pid>);

-- Analyze slow queries
EXPLAIN (ANALYZE, BUFFERS) <slow_query>;
```

**Missing Indexes**
```sql
-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public' AND n_distinct > 100 AND correlation < 0.1;
```

### Database Backup and Recovery

#### Backup Failures

**Diagnosis**
```bash
# Check backup cron job
kubectl get cronjobs -n pathavana-production
kubectl get jobs -n pathavana-production

# Check backup logs
kubectl logs job/database-backup-<timestamp> -n pathavana-production
```

**Solutions**
```bash
# Manual backup
kubectl create job manual-backup-$(date +%Y%m%d) --from=cronjob/database-backup -n pathavana-production

# Check backup storage
kubectl exec -it deployment/postgres -n pathavana-production -- ls -la /backups/
```

#### Database Recovery

**Point-in-Time Recovery**
```bash
# Stop application
kubectl scale deployment pathavana-backend --replicas=0 -n pathavana-production

# Restore from backup
kubectl exec -it deployment/postgres -n pathavana-production -- pg_restore -d pathavana /backups/latest.sql

# Start application
kubectl scale deployment pathavana-backend --replicas=3 -n pathavana-production
```

## Network and Connectivity

### Ingress Issues

#### Symptoms
- 502 Bad Gateway errors
- SSL certificate issues
- Routing problems

#### Diagnosis

1. **Check Ingress Status**
   ```bash
   kubectl get ingress -n pathavana-production
   kubectl describe ingress pathavana-ingress -n pathavana-production
   ```

2. **Check Ingress Controller**
   ```bash
   kubectl logs -f deployment/nginx-ingress-controller -n ingress-nginx
   ```

3. **Test Backend Services**
   ```bash
   kubectl port-forward service/pathavana-backend 8080:8000 -n pathavana-production
   curl http://localhost:8080/health
   ```

#### Common Solutions

**SSL Certificate Issues**
```bash
# Check certificate status
kubectl describe certificate tls-secret -n pathavana-production

# Force certificate renewal
kubectl delete certificate tls-secret -n pathavana-production
```

**Service Discovery Issues**
```bash
# Check service endpoints
kubectl get endpoints -n pathavana-production
kubectl describe service pathavana-backend -n pathavana-production
```

### DNS Issues

#### Symptoms
- Cannot resolve domain names
- Intermittent connectivity

#### Diagnosis

1. **Test DNS Resolution**
   ```bash
   kubectl exec -it deployment/pathavana-backend -n pathavana-production -- nslookup google.com
   kubectl exec -it deployment/pathavana-backend -n pathavana-production -- nslookup pathavana-backend.pathavana-production.svc.cluster.local
   ```

2. **Check CoreDNS**
   ```bash
   kubectl logs -f deployment/coredns -n kube-system
   ```

#### Solutions

**DNS Cache Issues**
```bash
# Restart CoreDNS
kubectl rollout restart deployment/coredns -n kube-system

# Clear DNS cache in pods
kubectl exec -it deployment/pathavana-backend -n pathavana-production -- resolvectl flush-caches
```

## Performance Issues

### High Response Times

#### Diagnosis Process

1. **Identify Bottlenecks**
   ```bash
   # Check application metrics
   curl -s http://prometheus:9090/api/v1/query?query='histogram_quantile(0.95,rate(http_request_duration_seconds_bucket[5m]))'
   
   # Check database performance
   kubectl exec -it deployment/postgres -n pathavana-production -- psql -U postgres -d pathavana -c "
   SELECT query, mean_time, calls, total_time 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 5;"
   ```

2. **Analyze Resource Usage**
   ```bash
   kubectl top pods -n pathavana-production
   kubectl top nodes
   ```

3. **Check External API Performance**
   ```bash
   # Check external API response times
   kubectl logs -f deployment/pathavana-backend -n pathavana-production | grep -i "external_api"
   ```

#### Optimization Steps

**Scale Application**
```bash
# Horizontal scaling
kubectl scale deployment pathavana-backend --replicas=5 -n pathavana-production

# Vertical scaling
kubectl patch deployment pathavana-backend -n pathavana-production -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "backend",
          "resources": {
            "limits": {"cpu": "2", "memory": "4Gi"},
            "requests": {"cpu": "1", "memory": "2Gi"}
          }
        }]
      }
    }
  }
}'
```

**Database Optimization**
```sql
-- Create missing indexes
CREATE INDEX CONCURRENTLY idx_bookings_user_id ON bookings(user_id);
CREATE INDEX CONCURRENTLY idx_sessions_created_at ON sessions(created_at);

-- Update table statistics
ANALYZE;

-- Optimize configuration
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
```

### Memory Issues

#### Symptoms
- Out of Memory (OOM) kills
- High memory usage
- Pod evictions

#### Diagnosis

1. **Check Memory Usage**
   ```bash
   kubectl top pods -n pathavana-production --sort-by=memory
   kubectl describe node <node-name> | grep -A 10 "Allocated resources"
   ```

2. **Check OOM Events**
   ```bash
   kubectl get events -n pathavana-production | grep -i oom
   dmesg | grep -i "killed process"
   ```

#### Solutions

**Increase Memory Limits**
```bash
kubectl patch deployment pathavana-backend -n pathavana-production -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "backend",
          "resources": {
            "limits": {"memory": "4Gi"},
            "requests": {"memory": "2Gi"}
          }
        }]
      }
    }
  }
}'
```

**Memory Leak Investigation**
```bash
# Monitor memory usage over time
kubectl exec -it deployment/pathavana-backend -n pathavana-production -- python -c "
import psutil
import time
for i in range(10):
    mem = psutil.virtual_memory()
    print(f'Memory usage: {mem.percent}% ({mem.used/1024/1024:.1f}MB used)')
    time.sleep(30)
"
```

## Security Issues

### Authentication Failures

#### Symptoms
- High number of failed login attempts
- Suspicious login patterns
- Token validation errors

#### Investigation Steps

1. **Check Authentication Logs**
   ```bash
   kubectl logs -f deployment/pathavana-backend -n pathavana-production | grep -E "(auth|login|token)" | tail -100
   ```

2. **Check Failed Login Patterns**
   ```sql
   SELECT 
     client_ip, 
     COUNT(*) as failed_attempts,
     MIN(created_at) as first_attempt,
     MAX(created_at) as last_attempt
   FROM auth_logs 
   WHERE success = false 
     AND created_at > NOW() - INTERVAL '1 hour'
   GROUP BY client_ip 
   HAVING COUNT(*) > 10
   ORDER BY failed_attempts DESC;
   ```

#### Response Actions

**Block Suspicious IPs**
```bash
# Add IP to network policy deny list
kubectl patch networkpolicy pathavana-backend-policy -n pathavana-production --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/ingress/0/from/-",
    "value": {
      "podSelector": {},
      "except": [{"ipBlock": {"cidr": "192.168.1.100/32"}}]
    }
  }
]'
```

**Reset User Sessions**
```sql
-- Revoke all sessions for compromised user
DELETE FROM user_sessions WHERE user_id = '<user_id>';

-- Force password reset
UPDATE users SET password_reset_required = true WHERE id = '<user_id>';
```

### Data Breach Investigation

#### Immediate Response

1. **Isolate Affected Systems**
   ```bash
   # Scale down affected services
   kubectl scale deployment pathavana-backend --replicas=0 -n pathavana-production
   
   # Block external access
   kubectl patch service pathavana-backend -n pathavana-production -p '{"spec":{"type":"ClusterIP"}}'
   ```

2. **Preserve Evidence**
   ```bash
   # Create forensic backup
   kubectl create job forensic-backup-$(date +%Y%m%d-%H%M) --from=cronjob/database-backup -n pathavana-production
   
   # Export logs
   kubectl logs deployment/pathavana-backend -n pathavana-production --since=24h > incident-logs-$(date +%Y%m%d).log
   ```

3. **Assess Damage**
   ```sql
   -- Check data access patterns
   SELECT 
     user_id, 
     action, 
     resource_type,
     COUNT(*) as access_count,
     MIN(created_at) as first_access,
     MAX(created_at) as last_access
   FROM audit_logs 
   WHERE created_at > NOW() - INTERVAL '24 hours'
   GROUP BY user_id, action, resource_type
   ORDER BY access_count DESC;
   ```

## Deployment Issues

### Failed Deployments

#### Symptoms
- Pods stuck in ImagePullBackOff
- Deployment rollout failures
- Configuration errors

#### Diagnosis

1. **Check Deployment Status**
   ```bash
   kubectl rollout status deployment/pathavana-backend -n pathavana-production
   kubectl describe deployment pathavana-backend -n pathavana-production
   ```

2. **Check ReplicaSet Events**
   ```bash
   kubectl get rs -n pathavana-production
   kubectl describe rs <replicaset-name> -n pathavana-production
   ```

#### Common Solutions

**Image Pull Failures**
```bash
# Check image exists
docker pull ghcr.io/pathavana/pathavana-backend:latest

# Update image pull secret
kubectl delete secret registry-secret -n pathavana-production
kubectl create secret docker-registry registry-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n pathavana-production
```

**Configuration Errors**
```bash
# Validate configuration
kubectl apply --dry-run=client -f k8s/production/

# Check ConfigMap and Secret references
kubectl get configmap,secret -n pathavana-production
```

**Rollback Failed Deployment**
```bash
# Check rollout history
kubectl rollout history deployment/pathavana-backend -n pathavana-production

# Rollback to previous version
kubectl rollout undo deployment/pathavana-backend -n pathavana-production

# Rollback to specific revision
kubectl rollout undo deployment/pathavana-backend --to-revision=2 -n pathavana-production
```

### Blue-Green Deployment Issues

#### Failed Traffic Switch

**Diagnosis**
```bash
# Check service selector
kubectl get service pathavana-backend -n pathavana-production -o yaml | grep selector

# Check pod labels
kubectl get pods -n pathavana-production -l app=pathavana --show-labels
```

**Recovery**
```bash
# Switch back to blue deployment
kubectl patch service pathavana-backend -n pathavana-production -p '{"spec":{"selector":{"version":"blue"}}}'

# Scale up blue deployment
kubectl scale deployment pathavana-backend-blue --replicas=3 -n pathavana-production
```

## Monitoring and Alerting

### Missing Metrics

#### Symptoms
- Gaps in Grafana dashboards
- Missing alert data
- Prometheus targets down

#### Diagnosis

1. **Check Prometheus Targets**
   ```bash
   curl -s http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'
   ```

2. **Check Service Discovery**
   ```bash
   kubectl get servicemonitor -A
   kubectl get endpoints -n pathavana-production
   ```

3. **Check Metrics Endpoints**
   ```bash
   kubectl port-forward service/pathavana-backend 8080:8000 -n pathavana-production
   curl http://localhost:8080/metrics
   ```

#### Solutions

**Fix Service Discovery**
```bash
# Check service labels
kubectl get service pathavana-backend -n pathavana-production --show-labels

# Update ServiceMonitor
kubectl apply -f monitoring/servicemonitor.yaml
```

**Restart Prometheus**
```bash
kubectl rollout restart deployment/prometheus -n monitoring
```

### Alert Fatigue

#### Symptoms
- Too many alerts firing
- Alerts not being acknowledged
- Important alerts missed

#### Solutions

1. **Review Alert Thresholds**
   ```yaml
   # Adjust alert thresholds
   - alert: HighErrorRate
     expr: rate(http_requests_total{code=~"5.."}[5m]) > 0.05  # Increase from 0.01
     for: 5m  # Increase from 1m
   ```

2. **Implement Alert Routing**
   ```yaml
   # Route non-critical alerts differently
   routes:
   - match:
       severity: warning
     receiver: 'slack-warnings'
     group_wait: 30s
     repeat_interval: 4h
   ```

3. **Use Alert Inhibition**
   ```yaml
   # Inhibit lower severity alerts when critical alerts fire
   inhibit_rules:
   - source_match:
       severity: critical
     target_match:
       severity: warning
     equal: ['alertname', 'instance']
   ```

## Emergency Procedures

### Complete Service Outage

#### Immediate Actions (0-5 minutes)

1. **Assess Scope**
   ```bash
   # Check all services
   kubectl get pods -A | grep -v Running
   curl -I https://pathavana.com/health
   ```

2. **Check Infrastructure**
   ```bash
   # Check nodes
   kubectl get nodes
   
   # Check critical pods
   kubectl get pods -n kube-system
   kubectl get pods -n pathavana-production
   ```

3. **Notify Stakeholders**
   ```bash
   # Send alert to Slack
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"🚨 CRITICAL: Pathavana service outage detected"}' \
     $SLACK_WEBHOOK_URL
   ```

#### Investigation (5-15 minutes)

1. **Check Recent Changes**
   ```bash
   # Check deployment history
   kubectl rollout history deployment/pathavana-backend -n pathavana-production
   
   # Check recent events
   kubectl get events -n pathavana-production --sort-by='.lastTimestamp' | tail -20
   ```

2. **Check External Dependencies**
   ```bash
   # Test external APIs
   curl -I https://api.openai.com/v1/models
   curl -I https://api.amadeus.com/v1/security/oauth2/token
   ```

3. **Check Infrastructure Health**
   ```bash
   # Check AWS services
   aws eks describe-cluster --name pathavana-prod-cluster
   aws rds describe-db-instances --db-instance-identifier pathavana-prod-postgres
   ```

#### Recovery Actions (15-30 minutes)

1. **Quick Fixes**
   ```bash
   # Restart deployments
   kubectl rollout restart deployment/pathavana-backend -n pathavana-production
   kubectl rollout restart deployment/pathavana-frontend -n pathavana-production
   
   # Scale up if needed
   kubectl scale deployment pathavana-backend --replicas=5 -n pathavana-production
   ```

2. **Rollback if Necessary**
   ```bash
   # Rollback to last known good version
   kubectl rollout undo deployment/pathavana-backend -n pathavana-production
   kubectl rollout undo deployment/pathavana-frontend -n pathavana-production
   ```

3. **Activate Disaster Recovery**
   ```bash
   # If primary region is down, activate secondary region
   aws route53 change-resource-record-sets --hosted-zone-id Z123456789 \
     --change-batch file://failover-dns.json
   ```

### Data Loss Incident

#### Immediate Response

1. **Stop All Writes**
   ```bash
   # Scale backend to 0 to prevent further data loss
   kubectl scale deployment pathavana-backend --replicas=0 -n pathavana-production
   ```

2. **Assess Damage**
   ```sql
   -- Check recent data modifications
   SELECT 
     table_name,
     n_tup_ins as inserts,
     n_tup_upd as updates, 
     n_tup_del as deletes
   FROM pg_stat_user_tables 
   WHERE schemaname = 'public';
   ```

3. **Secure Evidence**
   ```bash
   # Create forensic database dump
   kubectl exec -it deployment/postgres -n pathavana-production -- pg_dump -U postgres pathavana > forensic-dump-$(date +%Y%m%d-%H%M).sql
   ```

#### Recovery Process

1. **Restore from Backup**
   ```bash
   # Find latest backup
   kubectl exec -it deployment/postgres -n pathavana-production -- ls -la /backups/
   
   # Restore database
   kubectl exec -it deployment/postgres -n pathavana-production -- psql -U postgres -c "DROP DATABASE pathavana;"
   kubectl exec -it deployment/postgres -n pathavana-production -- psql -U postgres -c "CREATE DATABASE pathavana;"
   kubectl exec -it deployment/postgres -n pathavana-production -- pg_restore -U postgres -d pathavana /backups/latest.sql
   ```

2. **Verify Data Integrity**
   ```sql
   -- Check record counts
   SELECT 'users' as table_name, COUNT(*) FROM users
   UNION ALL
   SELECT 'bookings', COUNT(*) FROM bookings
   UNION ALL
   SELECT 'sessions', COUNT(*) FROM sessions;
   ```

3. **Restart Services**
   ```bash
   # Gradually restore service
   kubectl scale deployment pathavana-backend --replicas=1 -n pathavana-production
   
   # Test functionality
   curl -f https://pathavana.com/api/v1/health
   
   # Scale to full capacity
   kubectl scale deployment pathavana-backend --replicas=3 -n pathavana-production
   ```

### Security Incident Response

#### Containment

1. **Isolate Affected Systems**
   ```bash
   # Block external access
   kubectl patch ingress pathavana-ingress -n pathavana-production -p '{"spec":{"rules":[]}}'
   
   # Scale down affected services
   kubectl scale deployment pathavana-backend --replicas=0 -n pathavana-production
   ```

2. **Preserve Evidence**
   ```bash
   # Export all logs
   kubectl logs deployment/pathavana-backend -n pathavana-production --since=24h > security-incident-logs.txt
   
   # Create database snapshot
   kubectl create job security-backup-$(date +%Y%m%d) --from=cronjob/database-backup -n pathavana-production
   ```

#### Investigation

1. **Analyze Attack Vectors**
   ```bash
   # Check access logs
   kubectl logs -f deployment/nginx-ingress-controller -n ingress-nginx | grep -E "(40[0-9]|50[0-9])"
   ```

2. **Check for Compromise**
   ```sql
   -- Check for suspicious database activity
   SELECT 
     usename,
     application_name,
     client_addr,
     state,
     query_start,
     query
   FROM pg_stat_activity 
   WHERE state != 'idle'
   ORDER BY query_start;
   ```

#### Recovery

1. **Security Hardening**
   ```bash
   # Force password resets
   kubectl exec -it deployment/pathavana-backend -n pathavana-production -- python scripts/force_password_reset.py
   
   # Rotate all secrets
   kubectl delete secret pathavana-secrets -n pathavana-production
   kubectl apply -f security/secrets/new-sealed-secrets.yaml
   ```

2. **Gradual Restoration**
   ```bash
   # Restore with enhanced monitoring
   kubectl apply -f security/enhanced-monitoring.yaml
   kubectl scale deployment pathavana-backend --replicas=1 -n pathavana-production
   ```

---

**Emergency Contacts:**
- **Incident Commander**: +1-XXX-XXX-XXXX
- **Technical Lead**: +1-XXX-XXX-XXXX  
- **Security Team**: security@pathavana.com
- **Executive Team**: executives@pathavana.com

Remember: Document everything during an incident for post-mortem analysis.