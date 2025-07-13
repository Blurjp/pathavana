# Terraform Outputs for Pathavana Infrastructure

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

# EKS Outputs
output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
}

output "cluster_version" {
  description = "EKS cluster version"
  value       = module.eks.cluster_version
}

output "node_groups" {
  description = "EKS node groups"
  value       = module.eks.node_groups
}

# Database Outputs
output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "db_instance_port" {
  description = "RDS instance port"
  value       = module.rds.db_instance_port
}

output "db_instance_id" {
  description = "RDS instance ID"
  value       = module.rds.db_instance_id
}

output "db_instance_arn" {
  description = "RDS instance ARN"
  value       = module.rds.db_instance_arn
}

# Redis Outputs
output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.elasticache.redis_endpoint
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = module.elasticache.redis_port
}

# Load Balancer Outputs
output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.dns_name
}

output "alb_zone_id" {
  description = "ALB zone ID"
  value       = module.alb.zone_id
}

output "alb_arn" {
  description = "ALB ARN"
  value       = module.alb.arn
}

# DNS Outputs
output "domain_name" {
  description = "Domain name"
  value       = var.domain_name
}

output "subdomain_name" {
  description = "Full subdomain name"
  value       = module.route53.subdomain_name
}

output "route53_zone_id" {
  description = "Route 53 hosted zone ID"
  value       = module.route53.zone_id
}

# S3 Outputs
output "assets_bucket_id" {
  description = "Assets S3 bucket ID"
  value       = module.s3.assets_bucket_id
}

output "backup_bucket_id" {
  description = "Backup S3 bucket ID"
  value       = module.s3.backup_bucket_id
}

output "logs_bucket_id" {
  description = "Logs S3 bucket ID"
  value       = module.s3.logs_bucket_id
}

# ECR Outputs
output "backend_ecr_repository_url" {
  description = "Backend ECR repository URL"
  value       = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_repository_url" {
  description = "Frontend ECR repository URL"
  value       = aws_ecr_repository.frontend.repository_url
}

# Secrets Manager Outputs
output "secrets_manager_arns" {
  description = "ARNs of secrets in AWS Secrets Manager"
  value       = module.secrets.secret_arns
  sensitive   = true
}

# Security Groups Outputs
output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = module.security_groups.alb_sg_id
}

output "eks_security_group_id" {
  description = "EKS security group ID"
  value       = module.security_groups.eks_sg_id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = module.security_groups.rds_sg_id
}

output "elasticache_security_group_id" {
  description = "ElastiCache security group ID"
  value       = module.security_groups.elasticache_sg_id
}

# Monitoring Outputs
output "cloudwatch_log_groups" {
  description = "CloudWatch log groups"
  value       = module.cloudwatch.log_groups
}

output "prometheus_endpoint" {
  description = "Prometheus endpoint"
  value       = var.enable_monitoring ? module.monitoring.prometheus_endpoint : null
}

output "grafana_endpoint" {
  description = "Grafana endpoint"
  value       = var.enable_monitoring ? module.monitoring.grafana_endpoint : null
}

# Cost Optimization Outputs
output "estimated_monthly_cost" {
  description = "Estimated monthly cost in USD"
  value = {
    eks_cluster = "~$73/month"
    eks_nodes   = "~$30/month per t3.medium node"
    rds         = "~$15/month for db.t3.micro"
    elasticache = "~$12/month for cache.t3.micro"
    alb         = "~$16/month"
    nat_gateway = "~$32/month"
    data_transfer = "Variable based on usage"
    total_estimated = "~$200-400/month for production environment"
  }
}

# Environment Information
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "deployment_info" {
  description = "Deployment information"
  value = {
    environment    = var.environment
    region        = var.aws_region
    cluster_name  = module.eks.cluster_name
    domain        = var.domain_name
    subdomain     = module.route53.subdomain_name
    alb_endpoint  = module.alb.dns_name
    created_at    = timestamp()
  }
}

# Connection Information for Applications
output "connection_info" {
  description = "Connection information for applications"
  value = {
    database_host = module.rds.db_instance_endpoint
    database_port = module.rds.db_instance_port
    database_name = var.db_name
    redis_host    = module.elasticache.redis_endpoint
    redis_port    = module.elasticache.redis_port
    cluster_name  = module.eks.cluster_name
    namespace     = "pathavana-${var.environment}"
  }
  sensitive = true
}

# Kubectl Configuration Command
output "kubectl_config" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}