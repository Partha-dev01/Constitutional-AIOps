# Import-only adoption of the EXISTING AIOps infrastructure.
#
# SAFETY MODEL — every adopted resource carries:
#     lifecycle { prevent_destroy = true, ignore_changes = all }
# so Terraform will NEVER recreate or mutate the live instance / EIP / volumes.
# The config-driven `import` blocks bring them into state on the first
# `terraform apply`; `ignore_changes = all` then suppresses every attribute diff.
#
# The ONLY new (additive) resources are the 80/443 ingress rules for Caddy.
# vLLM ports 8000/8001 are deliberately NOT opened to the world — they stay
# private (existing SG rules untouched), reachable only through Caddy on 443.
#
# EXPECTED `terraform plan` AFTER init: only the two SG ingress rules to add,
#   "0 to change, 0 to destroy". If anything proposes destroy/replace -> STOP.

# --- Existing security group (referenced for its ID, not managed) ---------
data "aws_security_group" "aiops" {
  filter {
    name   = "group-name"
    values = [var.security_group_name]
  }
}

# --- Adopt the EC2 instance ----------------------------------------------
import {
  to = aws_instance.aiops
  id = var.instance_id
}

resource "aws_instance" "aiops" {
  ami           = var.instance_ami
  instance_type = var.instance_type

  lifecycle {
    prevent_destroy = true
    ignore_changes  = all
  }

  tags = {
    Name = "aiops"
  }
}

# --- Adopt the held Elastic IP -------------------------------------------
import {
  to = aws_eip.aiops
  id = var.eip_allocation_id
}

resource "aws_eip" "aiops" {
  domain = "vpc"

  lifecycle {
    prevent_destroy = true
    ignore_changes  = all
  }
}

# --- Adopt the EBS volumes (root + data) ---------------------------------
import {
  to = aws_ebs_volume.root
  id = var.root_volume_id
}

resource "aws_ebs_volume" "root" {
  availability_zone = var.availability_zone
  size              = var.root_volume_size

  lifecycle {
    prevent_destroy = true
    ignore_changes  = all
  }
}

import {
  to = aws_ebs_volume.data
  id = var.data_volume_id
}

resource "aws_ebs_volume" "data" {
  availability_zone = var.availability_zone
  size              = var.data_volume_size

  lifecycle {
    prevent_destroy = true
    ignore_changes  = all
  }
}

# --- Additive: open 80/443 for Caddy + Let's Encrypt (Gate 6) ------------
resource "aws_vpc_security_group_ingress_rule" "http" {
  count             = var.manage_caddy_ports ? 1 : 0
  security_group_id = data.aws_security_group.aiops.id
  description       = "HTTP (Caddy / Let's Encrypt HTTP-01 challenge)"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "https" {
  count             = var.manage_caddy_ports ? 1 : 0
  security_group_id = data.aws_security_group.aiops.id
  description       = "HTTPS (Caddy -> app + grafana + ingest, all path-routed)"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  cidr_ipv4         = "0.0.0.0/0"
}
