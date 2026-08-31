terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }
}

# CloudFront, ACM-for-CloudFront, and Lambda@Edge all live in us-east-1. The lite
# tier is deployed there, so a single default provider is enough. If you ever move
# the compute to another region, add an aliased us-east-1 provider for the
# CloudFront/ACM resources and keep the instance in the compute region.
provider "aws" {
  region = var.region
}
