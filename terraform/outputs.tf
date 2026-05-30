output "instance_id" {
  description = "Adopted EC2 instance ID."
  value       = aws_instance.aiops.id
}

output "public_ip" {
  description = "Elastic IP (stable public address)."
  value       = aws_eip.aiops.public_ip
}

output "security_group_id" {
  description = "Security group ID the ingress rules attach to."
  value       = data.aws_security_group.aiops.id
}

output "app_url" {
  description = "Public HTTPS URL once Caddy is up (Gate 6)."
  value       = "https://${var.app_domain}"
}
