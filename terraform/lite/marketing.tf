# Front-door redesign R2: the always-on marketing origin.
#
# The marketing site (../../marketing) is built to static files and served from
# this private S3 bucket as the CloudFront DEFAULT behavior, so plain visits and
# crawlers hit S3 and NEVER wake the box. Only the `/launch` cache behavior
# routes to the wake Lambda (see main.tf / the distribution). Access is via an
# S3-type Origin Access Control; the bucket blocks all public access and only
# this distribution can read it.
#
# SAFETY MODEL (same as main.tf): these resources already exist (created out of
# band during the R2 cutover). They are IMPORTED here so Terraform tracks drift;
# they are otherwise plainly managed. The CloudFront DISTRIBUTION itself stays a
# read-only data source (main.tf) -- its origins/behaviors/DefaultRootObject are
# edited out of band via the AWS CLI (documented in ../../marketing/README.md),
# exactly like the Lambda's code+env. Terraform never rewrites the live
# distribution.

locals {
  marketing_distribution_arn = "arn:aws:cloudfront::${var.account_id}:distribution/${var.cloudfront_distribution_id}"
}

# --- S3-type OAC the distribution uses to sign requests to the bucket --------
import {
  to = aws_cloudfront_origin_access_control.marketing_s3
  id = var.marketing_s3_oac_id
}

resource "aws_cloudfront_origin_access_control" "marketing_s3" {
  name                              = "aiops-marketing-s3"
  description                       = "OAC for aiops marketing S3 origin"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# --- The marketing bucket (private) ------------------------------------------
import {
  to = aws_s3_bucket.marketing
  id = var.marketing_bucket_name
}

resource "aws_s3_bucket" "marketing" {
  bucket = var.marketing_bucket_name

  tags = {
    Name    = "aiops-marketing"
    Project = "constitutional-aiops"
  }
}

import {
  to = aws_s3_bucket_public_access_block.marketing
  id = var.marketing_bucket_name
}

resource "aws_s3_bucket_public_access_block" "marketing" {
  bucket                  = aws_s3_bucket.marketing.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy      = true
  restrict_public_buckets = true
}

import {
  to = aws_s3_bucket_ownership_controls.marketing
  id = var.marketing_bucket_name
}

resource "aws_s3_bucket_ownership_controls" "marketing" {
  bucket = aws_s3_bucket.marketing.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

import {
  to = aws_s3_bucket_server_side_encryption_configuration.marketing
  id = var.marketing_bucket_name
}

resource "aws_s3_bucket_server_side_encryption_configuration" "marketing" {
  bucket = aws_s3_bucket.marketing.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- Bucket policy: only THIS distribution may GetObject (via OAC) ------------
import {
  to = aws_s3_bucket_policy.marketing
  id = var.marketing_bucket_name
}

resource "aws_s3_bucket_policy" "marketing" {
  bucket = aws_s3_bucket.marketing.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontOACGet"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.marketing.arn}/*"
      Condition = {
        StringEquals = { "AWS:SourceArn" = local.marketing_distribution_arn }
      }
    }]
  })
}
