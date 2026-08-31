# Terraform

Two independent modules, one per deployment tier. Each **adopts** already-running
infrastructure (import-only, `prevent_destroy`) — neither provisions from scratch.
Pick the one that matches how you're running the app; run Terraform from inside that
subdirectory.

| Module | Tier | Use it for |
|---|---|---|
| [`lite/`](lite/) | **Lite (current)** | The low-cost, no-fixed-IP sleep/wake front door: CloudFront → wake Lambda → on-demand EC2 that sleeps when idle. This is the self-hostable deployment. |
| [`legacy/`](legacy/) | **Legacy (frozen)** | The original GPU host (`g6.xlarge` + Elastic IP + EBS volumes). Kept import-only so the frozen infra stays tracked; not part of the OSS self-host story. |

State files and `terraform.tfvars` are gitignored via the shared `.gitignore` at this
level, so it covers both modules. All AWS CLI / Terraform runs use the operator
profile (`AWS_PROFILE=aiops-operator`), never account root.

See each module's `README.md` for its safety gate and workflow.
