# Terraform (lite) — adopt the sleep/wake front door (import-only)

> **This is the LITE tier**: the low-cost deployment with **no fixed IP**
> (a branded front door → CloudFront → a wake-on-visit Lambda → an on-demand EC2
> box that sleeps when idle). It is the current, self-hostable
> deployment. The frozen GPU host lives in the sibling module `../legacy/`. Use
> exactly one module per working directory.

Like `../legacy/`, this module **adopts** already-running infrastructure — it does
**not** provision from scratch. The lite tier is stood up by hand (see `../../aws/`
and `../../docs/DEPLOYMENT.md`); Terraform's job here is to track it and make drift
visible.

## What it manages vs. references

| Resource | Terraform role |
|---|---|
| `aws_instance.lite` (the sleep/wake box) | **imported + frozen** (`prevent_destroy`, `ignore_changes = all`) |
| `aws_lambda_permission.cloudfront_invoke_url` | **managed** — `lambda:InvokeFunctionUrl` for CloudFront |
| `aws_lambda_permission.cloudfront_invoke_function` | **managed** — `lambda:InvokeFunction` for CloudFront |
| `data.aws_lambda_function.wake` | referenced (read-only) |
| `data.aws_cloudfront_distribution.front` | referenced (read-only) |
| `data.aws_security_group.lite` | referenced (read-only) |

### Why the two Lambda permissions are managed (not frozen)

An OAC → Lambda **Function URL** origin needs **both** `lambda:InvokeFunctionUrl`
**and** `lambda:InvokeFunction` granted to `cloudfront.amazonaws.com` (scoped to the
distribution). With only the first, CloudFront returns **403 AccessDeniedException**
even though the Function URL, OAC, origin-request policy, and the first statement all
look correct — the CloudFront service principal has no identity policy, so it relies
entirely on this resource policy. This bit us once (see `docs/ISSUES.md` **FD-006**).
Managing both statements here means a missing one shows up as a `terraform plan` diff
instead of a silent production 403.

## Not managed here (out of band, by design)

- **The Lambda's code + environment** (including the DNS-provider token) — deployed
  via `../../aws/lambda/wake_on_visit/` and `aws lambda update-function-*`. The token
  never enters Terraform state.
- **DNS.** The front-door hostname is a one-time CNAME → the CloudFront distribution
  on the DNS provider. The box's own A record is re-pointed on every wake **by the
  Lambda itself**. The provider forbids subdomain NS-delegation, so there is no cloud
  DNS zone for Terraform to own.

## Workflow (read-only until you choose to `apply`)

```bash
cd terraform/lite

# 1. Fill terraform.tfvars from the live account (read-only describe calls).
#    Use the operator profile, never account root.
AWS_PROFILE=aiops-operator ./discover.sh

# 2. Init + plan (the safety gate).
terraform init
terraform plan
```

### The safety gate

A healthy `terraform plan` **adopts** the box and the two Lambda permissions with
**0 to change, 0 to destroy** (the import blocks reconcile them into state). If the
plan proposes to **destroy** or **replace** the instance, or to **create** a Lambda
permission that should already exist, STOP and re-check `terraform.tfvars` — a wrong
`cloudfront_distribution_id` / `account_id` is the usual cause.

> `prevent_destroy = true` on the box is a hard backstop: any plan that tries to
> replace it fails outright.

## Notes

- State is local (`terraform.tfstate`) and gitignored (shared `../.gitignore`), as is
  `terraform.tfvars`. Move to an S3+DynamoDB backend for team use.
- This module intentionally does not recreate the front door; treat the hand-build
  steps in `aws/` + `docs/DEPLOYMENT.md` as the source of truth for provisioning, and
  this module as the tracker/guardrail.
