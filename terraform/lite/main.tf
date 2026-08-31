# Import-only adoption of the LITE tier (sleep/wake front door, no fixed IP).
#
# The lite tier is already deployed by hand; this module ADOPTS it so it's
# tracked and drift-visible. It does NOT provision from scratch.
#
# SAFETY MODEL:
#   * The EC2 box is imported and pinned with prevent_destroy + ignore_changes=all
#     (never recreated, never mutated by Terraform).
#   * The wake Lambda, its Function URL config, the CloudFront distribution, the
#     OAC and the ACM cert are REFERENCED read-only (data sources) — Terraform
#     never manages their internals.
#   * The ONLY resources Terraform actively manages are the TWO Lambda resource-
#     policy statements the front door needs (see below). They are deliberately
#     managed (not frozen) so `terraform plan` flags drift if either is missing.
#
# NOT managed here (out of band, by design):
#   * The Lambda's own code + environment (deployed via aws/lambda/wake_on_visit
#     + `aws lambda update-function-*`); the token never lands in Terraform state.
#   * DNS. The front-door CNAME (front_domain -> the distribution) is a one-time
#     manual record on the DNS provider; the box's A record (app_node_domain) is
#     kept current by the wake Lambda itself. The provider forbids subdomain NS
#     delegation, so there is no cloud DNS zone to manage. See ../lite/README.md.

data "aws_security_group" "lite" {
  filter {
    name   = "group-name"
    values = [var.security_group_name]
  }
}

# --- Adopt + freeze the lite EC2 box -------------------------------------
import {
  to = aws_instance.lite
  id = var.instance_id
}

resource "aws_instance" "lite" {
  ami           = var.instance_ami
  instance_type = var.instance_type

  lifecycle {
    prevent_destroy = true
    ignore_changes  = all
  }

  tags = {
    Name = "aiops-lite"
  }
}

# --- Reference (read-only) the deployed front-door pieces -----------------
data "aws_lambda_function" "wake" {
  function_name = var.lambda_function_name
}

data "aws_cloudfront_distribution" "front" {
  id = var.cloudfront_distribution_id
}

# --- The front door's Lambda resource policy (ACTIVELY MANAGED) -----------
#
# An OAC -> Lambda Function URL origin needs BOTH of these statements for the
# CloudFront service principal. With only the first, CloudFront gets a
# 403 AccessDeniedException even though every other setting looks correct
# (the CloudFront service principal has no identity policy, so it relies wholly
# on this resource policy). See docs/ISSUES.md FD-006. Keeping both here means a
# missing statement shows up as a Terraform diff instead of a silent 403.
locals {
  distribution_source_arn = "arn:aws:cloudfront::${var.account_id}:distribution/${var.cloudfront_distribution_id}"
}

import {
  to = aws_lambda_permission.cloudfront_invoke_url
  id = "${var.lambda_function_name}/AllowCloudFrontOAC"
}

resource "aws_lambda_permission" "cloudfront_invoke_url" {
  statement_id           = "AllowCloudFrontOAC"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = var.lambda_function_name
  principal              = "cloudfront.amazonaws.com"
  source_arn             = local.distribution_source_arn
  function_url_auth_type = "AWS_IAM"
}

import {
  to = aws_lambda_permission.cloudfront_invoke_function
  id = "${var.lambda_function_name}/AllowCloudFrontInvokeFunction"
}

resource "aws_lambda_permission" "cloudfront_invoke_function" {
  statement_id  = "AllowCloudFrontInvokeFunction"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "cloudfront.amazonaws.com"
  source_arn    = local.distribution_source_arn
}
