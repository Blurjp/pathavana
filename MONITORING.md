# Pathavana Monitoring and Observability

This document describes the comprehensive monitoring, logging, and observability strategy for the Pathavana application.

## Table of Contents

- [Monitoring Overview](#monitoring-overview)
- [Metrics Collection](#metrics-collection)
- [Logging Strategy](#logging-strategy)
- [Distributed Tracing](#distributed-tracing)
- [Alerting and Notifications](#alerting-and-notifications)
- [Performance Monitoring](#performance-monitoring)
- [Security Monitoring](#security-monitoring)
- [Business Metrics](#business-metrics)
- [Dashboards](#dashboards)
- [Troubleshooting Guide](#troubleshooting-guide)

## Monitoring Overview

### Observability Pillars

The Pathavana monitoring strategy is built on the three pillars of observability:

1. **Metrics**: Quantitative measurements of system behavior
2. **Logs**: Discrete events with context and details
3. **Traces**: Request flow through distributed systems

### Monitoring Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                     Visualization Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Grafana   │  │   Kibana    │  │  Jaeger UI  │             │
│  │ (Metrics)   │  │   (Logs)    │  │  (Traces)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────┬───────────────────┬───────────────────────┘
                      │                   │
┌─────────────────────▼───────────────────▼───────────────────────┐
│                   Processing Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Prometheus  │  │Elasticsearch│  │   Jaeger    │             │
│  │  (Metrics)  │  │   (Logs)    │  │  (Traces)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────┬───────────────────┬───────────────────────┘
                      │                   │
┌─────────────────────▼───────────────────▼───────────────────────┐
│                   Collection Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Exporters │  │   Fluentd   │  │ OpenTelemetry│             │
│  │  (Metrics)  │  │   (Logs)    │  │  (Traces)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Metrics Collection

### Application Metrics

#### Custom Business Metrics

```python
# Backend metrics examples (FastAPI with Prometheus)
from prometheus_client import Counter, Histogram, Gauge

# User activity metrics
user_registrations = Counter('pathavana_user_registrations_total', 
                            'Total number of user registrations')
active_sessions = Gauge('pathavana_active_sessions', 
                       'Number of active user sessions')

# Travel booking metrics
booking_requests = Counter('pathavana_booking_requests_total', 
                          'Total booking requests', ['booking_type'])
booking_success = Counter('pathavana_booking_success_total', 
                         'Successful bookings', ['booking_type'])
booking_failures = Counter('pathavana_booking_failures_total', 
                          'Failed bookings', ['booking_type', 'error_type'])

# API performance metrics
request_duration = Histogram('pathavana_request_duration_seconds',
                           'Request duration', ['method', 'endpoint'])
external_api_calls = Counter('pathavana_external_api_calls_total',
                           'External API calls', ['provider', 'status'])
```

#### Standard HTTP Metrics

- **Request Rate**: Requests per second
- **Response Time**: P50, P95, P99 percentiles
- **Error Rate**: 4xx and 5xx error percentages
- **Throughput**: Requests processed per minute

#### Database Metrics

```sql
-- PostgreSQL metrics exposed via postgres_exporter
SELECT 
  schemaname,
  tablename,
  n_tup_ins as inserts,
  n_tup_upd as updates,
  n_tup_del as deletes,
  n_tup_hot_upd as hot_updates
FROM pg_stat_user_tables;
```

### Infrastructure Metrics

#### Kubernetes Metrics

- **Pod Metrics**: CPU, memory, disk usage
- **Node Metrics**: Resource utilization, capacity
- **Cluster Metrics**: Pod count, resource requests/limits
- **Service Metrics**: Endpoint availability, latency

#### System Metrics

- **CPU Usage**: Per core and aggregate
- **Memory Usage**: Used, available, swap
- **Disk Usage**: Space, IOPS, latency
- **Network**: Throughput, packet loss, connections

### External Service Metrics

#### API Integration Health

```python
# Monitor external API health
openai_api_health = Gauge('pathavana_openai_api_health', 
                         'OpenAI API health status')
amadeus_api_health = Gauge('pathavana_amadeus_api_health', 
                          'Amadeus API health status')
```

## Logging Strategy

### Log Levels and Usage

#### ERROR
- Application exceptions and errors
- External API failures
- Database connection issues
- Authentication failures

```python
logger.error("Failed to process booking", 
             extra={
                 "user_id": user.id,
                 "booking_id": booking.id,
                 "error": str(e),
                 "stack_trace": traceback.format_exc()
             })
```

#### WARN
- Deprecated API usage
- Performance degradation
- Rate limiting triggered
- Configuration issues

```python
logger.warning("API rate limit approaching", 
               extra={
                   "provider": "openai",
                   "current_rate": current_rate,
                   "limit": rate_limit
               })
```

#### INFO
- User actions (login, booking, search)
- System events (startup, shutdown)
- Business events (successful transactions)

```python
logger.info("User booking completed successfully",
            extra={
                "user_id": user.id,
                "booking_type": "flight",
                "destination": flight.destination,
                "amount": booking.total_amount
            })
```

#### DEBUG
- Detailed function entry/exit
- Variable states
- External API request/response details

### Structured Logging

All logs use JSON format with consistent fields:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "pathavana-backend",
  "version": "1.2.3",
  "trace_id": "abc123def456",
  "span_id": "789xyz",
  "user_id": "user_12345",
  "session_id": "session_67890",
  "message": "Flight search completed",
  "duration_ms": 245,
  "external_apis_called": ["amadeus"],
  "results_count": 15
}
```

### Log Aggregation Pipeline

#### Collection
- **Fluentd** agents on each node
- **Promtail** for Kubernetes pod logs
- **Filebeat** for system logs

#### Processing
- **Logstash** for log parsing and enrichment
- **Elasticsearch** for storage and indexing
- **Kibana** for visualization and analysis

#### Retention Policies
- **Real-time logs**: 7 days in hot storage
- **Recent logs**: 30 days in warm storage
- **Archived logs**: 12 months in cold storage
- **Compliance logs**: 7 years in glacier storage

## Distributed Tracing

### OpenTelemetry Integration

#### Automatic Instrumentation

```python
# FastAPI automatic instrumentation
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

app = FastAPI()

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Auto-instrument database
SQLAlchemyInstrumentor().instrument(engine=engine)

# Auto-instrument Redis
RedisInstrumentor().instrument()
```

#### Manual Instrumentation

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("process_flight_search")
def process_flight_search(search_params):
    span = trace.get_current_span()
    span.set_attribute("search.origin", search_params.origin)
    span.set_attribute("search.destination", search_params.destination)
    
    with tracer.start_as_current_span("call_amadeus_api") as api_span:
        api_span.set_attribute("external.service", "amadeus")
        results = amadeus_client.search_flights(search_params)
        api_span.set_attribute("results.count", len(results))
    
    return results
```

### Trace Analysis

#### Performance Analysis
- Identify slow operations across services
- Analyze external API call patterns
- Detect bottlenecks in request flow

#### Error Analysis
- Trace error propagation across services
- Identify root cause of failures
- Analyze error patterns and frequencies

## Alerting and Notifications

### Alert Severity Levels

#### P0 (Critical) - Immediate Response Required
- Service completely down
- Data loss or corruption
- Security breach detected
- External payment system failure

**Response Time**: < 5 minutes
**Notification**: Phone call, SMS, Slack, PagerDuty

#### P1 (High) - Urgent Response Required
- Significant performance degradation (>50% slower)
- High error rates (>5% for 5+ minutes)
- Database connection issues
- External API failures affecting user experience

**Response Time**: < 15 minutes
**Notification**: SMS, Slack, PagerDuty

#### P2 (Medium) - Response Required Within Hours
- Moderate performance degradation
- Elevated error rates (1-5%)
- Resource utilization warnings
- Non-critical feature failures

**Response Time**: < 2 hours
**Notification**: Slack, Email

#### P3 (Low) - Informational
- Maintenance reminders
- Capacity planning alerts
- Non-urgent configuration issues

**Response Time**: Next business day
**Notification**: Email

### Alert Rules Configuration

#### Application Alerts

```yaml
# High error rate alert
- alert: PathavanaHighErrorRate
  expr: |
    (
      rate(http_requests_total{job="pathavana-backend",code=~"5.."}[5m]) /
      rate(http_requests_total{job="pathavana-backend"}[5m])
    ) > 0.05
  for: 3m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }}"

# Slow response time alert
- alert: PathavanaSlowResponse
  expr: |
    histogram_quantile(0.95, 
      rate(http_request_duration_seconds_bucket{job="pathavana-backend"}[5m])
    ) > 2.0
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Slow response times detected"
    description: "95th percentile response time: {{ $value }}s"
```

#### Infrastructure Alerts

```yaml
# High CPU usage
- alert: HighCPUUsage
  expr: |
    100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "High CPU usage"
    description: "CPU usage is {{ $value }}%"

# Low disk space
- alert: LowDiskSpace
  expr: |
    (
      (node_filesystem_size_bytes - node_filesystem_free_bytes) / 
      node_filesystem_size_bytes
    ) > 0.85
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Low disk space"
    description: "Disk usage is {{ $value | humanizePercentage }}"
```

### Notification Channels

#### Slack Integration

```yaml
# AlertManager Slack configuration
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'slack-notifications'

receivers:
- name: 'slack-notifications'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/...'
    channel: '#pathavana-alerts'
    title: 'Pathavana Alert'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

#### PagerDuty Integration

```yaml
# PagerDuty configuration for critical alerts
- name: 'pagerduty-critical'
  pagerduty_configs:
  - routing_key: 'YOUR_PAGERDUTY_INTEGRATION_KEY'
    description: '{{ .GroupLabels.alertname }}'
    severity: '{{ .CommonLabels.severity }}'
```

## Performance Monitoring

### SLA/SLO Definitions

#### Service Level Objectives (SLOs)

| Metric | Target | Measurement Window |
|--------|--------|-------------------|
| Availability | 99.9% | 30 days |
| Response Time (P95) | < 2 seconds | 24 hours |
| Error Rate | < 1% | 24 hours |
| Throughput | > 100 req/min | Peak hours |

#### Error Budget
- **Monthly Error Budget**: 0.1% (43.2 minutes downtime)
- **Error Budget Alerts**: 50%, 75%, 90% consumption
- **Error Budget Policies**: Feature freeze when 100% consumed

### Performance Dashboards

#### Application Performance Dashboard

Key metrics displayed:
- Request rate and response time trends
- Error rate by endpoint
- Database query performance
- External API call success rates
- User session metrics

#### Infrastructure Performance Dashboard

Key metrics displayed:
- CPU and memory utilization
- Disk I/O and network throughput
- Kubernetes pod and node status
- Load balancer metrics
- Auto-scaling events

### Load Testing

#### Continuous Load Testing

```bash
# K6 load testing script
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 200 }, // Ramp up to 200 users
    { duration: '5m', target: 200 }, // Stay at 200 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% under 2s
    http_req_failed: ['rate<0.01'],    // Error rate under 1%
  },
};

export default function() {
  let response = http.get('https://pathavana.com/api/v1/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

## Security Monitoring

### Security Events

#### Authentication Events
- Failed login attempts
- Successful logins from new locations
- Password reset requests
- Account lockouts

#### Authorization Events
- Access denied events
- Privilege escalation attempts
- Suspicious API usage patterns

#### System Security Events
- Container security violations
- Network policy violations
- Secrets access events
- File system modifications

### Security Dashboards

#### Security Overview Dashboard
- Authentication success/failure rates
- Geographic distribution of logins
- API rate limiting events
- Suspicious activity alerts

#### Compliance Dashboard
- Data access logs
- Admin action audit trail
- Backup completion status
- Security scan results

### SIEM Integration

#### Log Sources
- Application authentication logs
- Kubernetes audit logs
- Network flow logs
- Container runtime logs

#### Correlation Rules
- Multiple failed logins from same IP
- Unusual API access patterns
- Privilege escalation attempts
- Data exfiltration patterns

## Business Metrics

### Key Performance Indicators (KPIs)

#### User Engagement
- Daily Active Users (DAU)
- Monthly Active Users (MAU)
- Session duration
- Page views per session
- User retention rates

#### Business Conversion
- Search-to-booking conversion rate
- Payment completion rate
- Average booking value
- Revenue per user

#### Operational Efficiency
- AI response accuracy rate
- External API success rates
- Customer support ticket volume
- Time to resolve issues

### Business Intelligence Dashboard

```sql
-- Example business metrics queries
-- Daily active users
SELECT 
  DATE(created_at) as date,
  COUNT(DISTINCT user_id) as dau
FROM user_sessions 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at);

-- Conversion funnel
SELECT 
  'searches' as stage, COUNT(*) as count
FROM travel_searches 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
UNION ALL
SELECT 
  'bookings_initiated', COUNT(*)
FROM bookings 
WHERE status = 'initiated' AND created_at >= CURRENT_DATE - INTERVAL '7 days'
UNION ALL
SELECT 
  'bookings_completed', COUNT(*)
FROM bookings 
WHERE status = 'completed' AND created_at >= CURRENT_DATE - INTERVAL '7 days';
```

## Dashboards

### Grafana Dashboard Organization

#### Folder Structure
```
├── Application/
│   ├── Pathavana Overview
│   ├── Backend Performance
│   ├── Frontend Analytics
│   └── External APIs
├── Infrastructure/
│   ├── Kubernetes Cluster
│   ├── Database Performance
│   ├── Cache Performance
│   └── Network Monitoring
├── Business/
│   ├── User Analytics
│   ├── Booking Metrics
│   └── Revenue Dashboard
└── Security/
    ├── Authentication Events
    ├── Security Incidents
    └── Compliance Metrics
```

#### Dashboard Standards
- **Refresh Rate**: 30 seconds for operational, 5 minutes for business
- **Time Range**: Last 1 hour default, with quick selectors
- **Templating**: Environment and service selection
- **Annotations**: Deploy events and incident markers

### Alert Dashboard
- Current active alerts
- Alert history and trends
- Alert acknowledgment status
- On-call schedule

## Troubleshooting Guide

### Common Issues and Solutions

#### High Response Times

1. **Check Application Metrics**
   ```bash
   # Query slow endpoints
   topk(5, rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]))
   ```

2. **Check Database Performance**
   ```sql
   SELECT query, mean_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC LIMIT 10;
   ```

3. **Check External API Performance**
   ```bash
   # Query external API response times
   histogram_quantile(0.95, rate(external_api_duration_seconds_bucket[5m]))
   ```

#### High Error Rates

1. **Identify Error Sources**
   ```bash
   # Top error endpoints
   topk(5, rate(http_requests_total{code=~"5.."}[5m]))
   ```

2. **Check Error Logs**
   ```bash
   kubectl logs -f deployment/pathavana-backend -n pathavana-production | grep ERROR
   ```

3. **Trace Error Propagation**
   - Use Jaeger to trace failed requests
   - Identify root cause service
   - Check external service dependencies

#### Resource Constraints

1. **CPU Bottlenecks**
   ```bash
   # Check CPU usage by pod
   kubectl top pods -n pathavana-production --sort-by=cpu
   ```

2. **Memory Issues**
   ```bash
   # Check memory usage
   kubectl top pods -n pathavana-production --sort-by=memory
   ```

3. **Storage Issues**
   ```bash
   # Check disk usage
   df -h /var/lib/docker
   ```

### Monitoring Health Checks

#### Daily Health Check Routine

```bash
#!/bin/bash
# Daily monitoring health check script

echo "=== Pathavana Monitoring Health Check ==="
echo "Date: $(date)"
echo

# Check Prometheus
echo "Checking Prometheus..."
curl -s http://prometheus:9090/-/healthy || echo "Prometheus UNHEALTHY"

# Check Grafana
echo "Checking Grafana..."
curl -s http://grafana:3000/api/health || echo "Grafana UNHEALTHY"

# Check AlertManager
echo "Checking AlertManager..."
curl -s http://alertmanager:9093/-/healthy || echo "AlertManager UNHEALTHY"

# Check active alerts
echo "Active alerts:"
curl -s http://alertmanager:9093/api/v1/alerts | jq '.data[] | select(.status.state=="active") | .labels.alertname'

# Check log pipeline
echo "Checking log pipeline..."
curl -s http://elasticsearch:9200/_cluster/health | jq '.status'

echo "=== Health Check Complete ==="
```

### Performance Optimization

#### Query Optimization
- Regularly review slow queries
- Optimize database indexes
- Cache frequently accessed data
- Implement query result pagination

#### Resource Optimization
- Right-size container resources
- Implement horizontal pod autoscaling
- Use resource quotas and limits
- Monitor resource utilization trends

---

For questions about monitoring and observability, contact the DevOps team at devops@pathavana.com or the monitoring channel in Slack: #pathavana-monitoring.