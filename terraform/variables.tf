# Values default to the known IDs from the existing deployment. Run ./discover.sh
# (read-only AWS calls) to fill the ones that must be looked up live
# (instance_ami, availability_zone, eip_allocation_id) into terraform.tfvars.

variable "region" {
  description = "AWS region of the existing AIOps deployment."
  type        = string
  default     = "us-east-1"
}

variable "instance_id" {
  description = "Existing EC2 instance ID to adopt (never recreated)."
  type        = string
  default     = "i-091c4de0e95d63154"
}

variable "instance_type" {
  description = "Instance type. Frozen by ignore_changes; declared for config validity only."
  type        = string
  default     = "g6.xlarge"
}

variable "instance_ami" {
  description = "AMI the instance was launched from. Run discover.sh; frozen by ignore_changes."
  type        = string
  default     = "ami-00000000000000000"
}

variable "availability_zone" {
  description = "AZ of the instance + EBS volumes (e.g. us-east-1a). Run discover.sh."
  type        = string
  default     = "us-east-1a"
}

variable "eip_allocation_id" {
  description = "Allocation ID (eipalloc-...) of the held Elastic IP 44.195.172.165. Run discover.sh."
  type        = string
  # No default: the alloc ID must be looked up. discover.sh writes it to terraform.tfvars.
}

variable "root_volume_id" {
  description = "Root EBS volume ID."
  type        = string
  default     = "vol-01714af69faebb973"
}

variable "data_volume_id" {
  description = "Data EBS volume ID (models / persistence)."
  type        = string
  default     = "vol-0ff075a7541026572"
}

variable "root_volume_size" {
  description = "Root EBS size (GiB). Frozen by ignore_changes; declared for HCL validity."
  type        = number
  default     = 100
}

variable "data_volume_size" {
  description = "Data EBS size (GiB). Frozen by ignore_changes; declared for HCL validity."
  type        = number
  default     = 200
}

variable "security_group_name" {
  description = "Name of the existing vLLM security group (referenced for its ID)."
  type        = string
  default     = "aiops-vllm-sg"
}

variable "app_domain" {
  description = "Public domain served by Caddy."
  type        = string
  default     = "aiops.imaginaerium.in"
}

variable "manage_caddy_ports" {
  description = "Add public 80/443 ingress for Caddy + Let's Encrypt (Gate 6). Additive only."
  type        = bool
  default     = true
}
