# Lite-tier variables. Real IDs live in terraform.tfvars (gitignored); the
# defaults here are placeholders so the config is valid to `validate`/`plan`
# without leaking infrastructure identifiers. Run ./discover.sh to write a
# terraform.tfvars from the live account (read-only describe calls).

variable "region" {
  description = "AWS region of the lite deployment (CloudFront/ACM require us-east-1)."
  type        = string
  default     = "us-east-1"
}

# --- Compute (the sleep/wake box) ----------------------------------------
variable "instance_id" {
  description = "Existing lite EC2 instance ID to adopt (never recreated)."
  type        = string
  default     = "i-0123456789abcdef0"
}

variable "instance_type" {
  description = "Lite instance type. Frozen by ignore_changes; declared for HCL validity."
  type        = string
  default     = "t3.medium"
}

variable "instance_ami" {
  description = "AMI the lite box was launched from. Run discover.sh; frozen by ignore_changes."
  type        = string
  default     = "ami-00000000000000000"
}

variable "security_group_name" {
  description = "Name of the existing lite security group (referenced for its ID, not managed)."
  type        = string
  default     = "aiops-lite-sg"
}

# --- Wake Lambda + Function URL ------------------------------------------
variable "lambda_function_name" {
  description = "Name of the deployed wake-on-visit Lambda (adopted, frozen)."
  type        = string
  default     = "aiops-wake-on-visit"
}

# --- Front door (CloudFront + OAC + ACM) ---------------------------------
variable "cloudfront_distribution_id" {
  description = "CloudFront distribution ID fronting the wake Lambda (adopted, frozen)."
  type        = string
  default     = "E1XXXXXXXXXXXX"
}

variable "origin_access_control_id" {
  description = "OAC ID (lambda origin type) attached to the distribution (adopted, frozen)."
  type        = string
  default     = "EXXXXXXXXXXXXX"
}

variable "front_domain" {
  description = "Public front-door hostname (CNAME -> the CloudFront distribution)."
  type        = string
  default     = "aiops.example.com"
}

variable "app_node_domain" {
  description = "The box's own hostname; the wake Lambda keeps its A record current."
  type        = string
  default     = "aiops-node.example.com"
}

variable "account_id" {
  description = "AWS account ID (used to build the distribution SourceArn in the Lambda policy)."
  type        = string
  default     = "000000000000"
}
