output "instance_id" {
  description = "Adopted lite EC2 instance ID (sleep/wake box)."
  value       = aws_instance.lite.id
}

output "security_group_id" {
  description = "Lite security group ID (referenced)."
  value       = data.aws_security_group.lite.id
}

output "lambda_function_arn" {
  description = "Wake-on-visit Lambda ARN (referenced)."
  value       = data.aws_lambda_function.wake.arn
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain the front_domain CNAME should point at."
  value       = data.aws_cloudfront_distribution.front.domain_name
}

output "front_url" {
  description = "Public front door (CloudFront, branded cert)."
  value       = "https://${var.front_domain}"
}

output "app_node_url" {
  description = "The box's own URL (302 target once awake; A record kept current by the Lambda)."
  value       = "https://${var.app_node_domain}"
}

output "marketing_bucket" {
  description = "Private S3 bucket serving the always-on marketing site (CloudFront default origin)."
  value       = aws_s3_bucket.marketing.id
}

output "marketing_s3_oac_id" {
  description = "S3-type OAC the distribution uses to read the marketing bucket."
  value       = aws_cloudfront_origin_access_control.marketing_s3.id
}
