# Pathavana Infrastructure as Code
# Main Terraform configuration for AWS deployment

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    # Backend configuration will be provided via backend config file
    # terraform init -backend-config=backend.hcl
  }
}

# Provider Configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Pathavana"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
    }
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# Data Sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local Values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  vpc_cidr = var.vpc_cidr
  azs      = slice(data.aws_availability_zones.available.names, 0, 3)
  
  private_subnets = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k)]
  public_subnets  = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k + 10)]
  
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name               = local.name_prefix
  cidr               = local.vpc_cidr
  azs                = local.azs
  private_subnets    = local.private_subnets
  public_subnets     = local.public_subnets
  enable_nat_gateway = true
  enable_vpn_gateway = false
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = local.tags
}

# EKS Module
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = "${local.name_prefix}-cluster"
  cluster_version = var.kubernetes_version
  
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  
  node_groups = {
    main = {
      instance_types = var.node_instance_types
      scaling_config = {
        desired_size = var.node_desired_size
        max_size     = var.node_max_size
        min_size     = var.node_min_size
      }
      capacity_type = "ON_DEMAND"
      disk_size     = 50
    }
    
    spot = {
      instance_types = var.spot_instance_types
      scaling_config = {
        desired_size = var.spot_desired_size
        max_size     = var.spot_max_size
        min_size     = var.spot_min_size
      }
      capacity_type = "SPOT"
      disk_size     = 50
    }
  }
  
  tags = local.tags
}

# RDS Module
module "rds" {
  source = "./modules/rds"
  
  identifier = "${local.name_prefix}-postgres"
  
  engine               = "postgres"
  engine_version       = var.postgres_version
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  
  db_name  = var.db_name
  username = var.db_username
  
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnets
  vpc_security_group_ids = [module.security_groups.rds_sg_id]
  
  backup_retention_period = var.db_backup_retention_period
  backup_window          = var.db_backup_window
  maintenance_window     = var.db_maintenance_window
  
  monitoring_interval = var.environment == "prod" ? 60 : 0
  
  tags = local.tags
}

# ElastiCache Module
module "elasticache" {
  source = "./modules/elasticache"
  
  cluster_id         = "${local.name_prefix}-redis"
  node_type         = var.redis_node_type
  num_cache_nodes   = var.redis_num_nodes
  parameter_group_name = "default.redis7"
  port              = 6379
  
  subnet_group_name = "${local.name_prefix}-redis-subnet-group"
  subnet_ids        = module.vpc.private_subnets
  security_group_ids = [module.security_groups.elasticache_sg_id]
  
  tags = local.tags
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security_groups"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  
  tags = local.tags
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  name               = "${local.name_prefix}-alb"
  vpc_id            = module.vpc.vpc_id
  subnets           = module.vpc.public_subnets
  security_groups   = [module.security_groups.alb_sg_id]
  
  certificate_arn   = var.ssl_certificate_arn
  
  tags = local.tags
}

# Route 53
module "route53" {
  source = "./modules/route53"
  
  domain_name        = var.domain_name
  subdomain_name     = var.subdomain_name
  alb_dns_name       = module.alb.dns_name
  alb_zone_id        = module.alb.zone_id
  
  tags = local.tags
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"
  
  bucket_prefix = local.name_prefix
  
  # Application assets bucket
  assets_bucket_name = "${local.name_prefix}-assets"
  
  # Backup bucket
  backup_bucket_name = "${local.name_prefix}-backups"
  
  # Logs bucket
  logs_bucket_name = "${local.name_prefix}-logs"
  
  tags = local.tags
}

# CloudWatch
module "cloudwatch" {
  source = "./modules/cloudwatch"
  
  name_prefix    = local.name_prefix
  cluster_name   = module.eks.cluster_name
  
  log_retention_days = var.log_retention_days
  
  tags = local.tags
}

# Monitoring and Observability
module "monitoring" {
  source = "./modules/monitoring"
  
  cluster_name   = module.eks.cluster_name
  namespace      = "monitoring"
  
  prometheus_storage_size = var.prometheus_storage_size
  grafana_admin_password  = var.grafana_admin_password
  
  tags = local.tags
}

# Secrets Manager
module "secrets" {
  source = "./modules/secrets"
  
  name_prefix = local.name_prefix
  
  secrets = {
    database = {
      description = "Database credentials"
      secret_string = jsonencode({
        username = var.db_username
        password = random_password.db_password.result
        endpoint = module.rds.db_instance_endpoint
        port     = module.rds.db_instance_port
        dbname   = var.db_name
      })
    }
    
    redis = {
      description = "Redis connection details"
      secret_string = jsonencode({
        endpoint = module.elasticache.redis_endpoint
        port     = module.elasticache.redis_port
      })
    }
    
    application = {
      description = "Application secrets"
      secret_string = jsonencode({
        secret_key = random_password.secret_key.result
        jwt_secret = random_password.jwt_secret.result
      })
    }
  }
  
  tags = local.tags
}

# Random passwords
resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "random_password" "secret_key" {
  length  = 64
  special = false
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

# ECR Repositories
resource "aws_ecr_repository" "backend" {
  name                 = "${local.name_prefix}-backend"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  lifecycle_policy {
    policy = jsonencode({
      rules = [
        {
          rulePriority = 1
          description  = "Keep last 30 images"
          selection = {
            tagStatus     = "tagged"
            tagPrefixList = ["v"]
            countType     = "imageCountMoreThan"
            countNumber   = 30
          }
          action = {
            type = "expire"
          }
        }
      ]
    })
  }
  
  tags = local.tags
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${local.name_prefix}-frontend"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  lifecycle_policy {
    policy = jsonencode({
      rules = [
        {
          rulePriority = 1
          description  = "Keep last 30 images"
          selection = {
            tagStatus     = "tagged"
            tagPrefixList = ["v"]
            countType     = "imageCountMoreThan"
            countNumber   = 30
          }
          action = {
            type = "expire"
          }
        }
      ]
    })
  }
  
  tags = local.tags
}