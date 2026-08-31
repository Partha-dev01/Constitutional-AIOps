# Terraform (legacy) — adopt the frozen GPU host (import-only)

> **This is the LEGACY tier**: the original GPU deployment (`g6.xlarge` + Elastic
> IP + EBS volumes) that the product no longer runs by default. It is kept here,
> import-only, so the frozen infrastructure stays tracked and drift-visible — it
> is **not** part of the self-host / OSS story. The current low-cost deployment is
> the sibling module `../lite/` (sleep/wake front door, no fixed IP). Pick exactly
> one module per working directory.

This module **imports** the already-running AWS resources into Terraform state so
they're tracked and drift-visible. It **never creates or recreates** the instance,
Elastic IP, or EBS volumes — every adopted resource is pinned with
`prevent_destroy = true` and `ignore_changes = all`.

The only thing this module *adds* is the **80/443 ingress** rules Caddy needs in
Gate 6. vLLM's 8000/8001 stay private (existing rules untouched).

## What gets adopted

| Resource | ID source |
|---|---|
| `aws_instance.aiops` | `i-0123456789abcdef0` (g6.xlarge, us-east-1) |
| `aws_eip.aiops` | EIP `203.0.113.10` (alloc ID via `discover.sh`) |
| `aws_ebs_volume.root` | `vol-0abcdef1234567890` |
| `aws_ebs_volume.data` | `vol-0123456789abcdef0` |
| `data.aws_security_group.aiops` | `aiops-vllm-sg` (referenced, not managed) |

## Prerequisites

- Terraform ≥ 1.6, AWS CLI configured with the account that owns the instance.
- **No instance start required** — every step here is read-only / metadata-only
  (the box can stay stopped). Nothing here incurs compute spend.

## Workflow (all read-only until you choose to `apply`)

```bash
cd terraform

# 1. Discover the looked-up values (AMI, AZ, EIP alloc id) -> terraform.tfvars
./discover.sh

# 2. Initialise the provider
terraform init

# 3. Plan — THE SAFETY GATE
terraform plan
```

### The safety gate

`terraform plan` **must** report only:

```
Plan: 2 to add, 0 to change, 0 to destroy.
```

…where the *2 to add* are `aws_vpc_security_group_ingress_rule.http` and
`.https`. The import blocks adopt the instance/EIP/volumes with **0 changes**
(thanks to `ignore_changes = all`).

> ⛔ If the plan proposes to **destroy** or **replace** anything, STOP and do not
> apply — re-check `terraform.tfvars`. `prevent_destroy = true` will also hard-fail
> any plan that tries to replace the protected resources, as a backstop.

### Apply (only with explicit GO — opens 80/443)

```bash
terraform apply        # imports state + adds the two ingress rules
```

Applying here does **not** start the instance or change the app — it only brings
the resources into state and opens 80/443 for Caddy. Starting the VM is a separate
step (`aws/start-vm.sh`) at Gate 8.

## Notes

- State is local (`terraform.tfstate`) and **gitignored** along with
  `terraform.tfvars`. Move to an S3+DynamoDB backend later if you want remote state.
- To re-freeze the SG (skip the Caddy ports), set `manage_caddy_ports = false`.
- This module is intentionally minimal — it adopts and protects existing infra; it
  is not a from-scratch provisioner.
