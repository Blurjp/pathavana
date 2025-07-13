# Terraform Variables for Pathavana Infrastructure

# Project Configuration
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "pathavana"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "owner" {
  description = "Owner of the infrastructure"
  type        = string
  default     = "pathavana-team"
}

# AWS Configuration
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# EKS Configuration
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "node_instance_types" {
  description = "Instance types for EKS node group"
  type        = list(string)
  default     = ["t3.medium", "t3.large"]
}

variable "node_desired_size" {
  description = "Desired number of nodes"
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of nodes"
  type        = number
  default     = 10
}

variable "node_min_size" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "spot_instance_types" {
  description = "Instance types for spot node group"
  type        = list(string)
  default     = ["t3.medium", "t3.large", "m5.large"]
}

variable "spot_desired_size" {
  description = "Desired number of spot nodes"
  type        = number
  default     = 0
}

variable "spot_max_size" {
  description = "Maximum number of spot nodes"
  type        = number
  default     = 5
}

variable "spot_min_size" {
  description = "Minimum number of spot nodes"
  type        = number
  default     = 0
}

# Database Configuration
variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15.4"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for RDS"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "pathavana"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
}

variable "db_backup_retention_period" {
  description = "Database backup retention period in days"
  type        = number
  default     = 7
}

variable "db_backup_window" {
  description = "Database backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "db_maintenance_window" {
  description = "Database maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

# Domain Configuration
variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "pathavana.com"
}

variable "subdomain_name" {
  description = "Subdomain for the environment"
  type        = string
  default     = ""
}

variable "ssl_certificate_arn" {
  description = "SSL certificate ARN"
  type        = string
  default     = ""
}

# Monitoring Configuration
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "prometheus_storage_size" {
  description = "Prometheus storage size"
  type        = string
  default     = "20Gi"
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
  default     = ""
}

# Cost Optimization
variable "enable_cost_optimization" {
  description = "Enable cost optimization features"
  type        = bool
  default     = false
}

variable "enable_spot_instances" {
  description = "Enable spot instances for non-critical workloads"
  type        = bool
  default     = false
}

# Security Configuration
variable "enable_waf" {
  description = "Enable AWS WAF"
  type        = bool
  default     = true
}

variable "enable_guardduty" {
  description = "Enable AWS GuardDuty"
  type        = bool
  default     = true
}

variable "enable_config" {
  description = "Enable AWS Config"
  type        = bool
  default     = false
}

# Backup Configuration
variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 30
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup"
  type        = bool
  default     = false
}

variable "backup_region" {
  description = "Backup region for cross-region backup"
  type        = string
  default     = "us-west-2"
}

# Feature Flags
variable "enable_autoscaling" {
  description = "Enable auto-scaling for applications"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable monitoring stack (Prometheus, Grafana)"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable centralized logging (ELK stack)"
  type        = bool
  default     = true
}

variable "enable_service_mesh" {
  description = "Enable service mesh (Istio)"
  type        = bool
  default     = false
}

# Performance Configuration
variable "enable_redis_cluster" {
  description = "Enable Redis cluster mode"
  type        = bool
  default     = false
}

variable "enable_read_replicas" {
  description = "Enable database read replicas"
  type        = bool
  default     = false
}

variable "num_read_replicas" {
  description = "Number of read replicas"
  type        = number
  default     = 1
}

# Development Configuration
variable "enable_bastion_host" {
  description = "Enable bastion host for development access"
  type        = bool
  default     = false
}

variable "enable_vpn" {
  description = "Enable VPN gateway"
  type        = bool
  default     = false
}

# Compliance and Governance
variable "enable_encryption_at_rest" {
  description = "Enable encryption at rest for all services"
  type        = bool
  default     = true
}

variable "enable_encryption_in_transit" {
  description = "Enable encryption in transit"
  type        = bool
  default     = true
}

variable "compliance_framework" {
  description = "Compliance framework (SOC2, HIPAA, PCI-DSS)"
  type        = string
  default     = "SOC2"
  validation {
    condition     = contains(["SOC2", "HIPAA", "PCI-DSS", "GDPR", ""], var.compliance_framework)
    error_message = "Compliance framework must be SOC2, HIPAA, PCI-DSS, GDPR, or empty."
  }
}

# Resource Tagging
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}