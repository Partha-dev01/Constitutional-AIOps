# Wake-on-visit Lambda (5c WS4)

The "wake" half of the lite tier's sleep/wake front door — no Elastic IP, so the
$2-3/mo target holds. Pairs with `aws/idle-check.sh` (the "stop when idle" half).

**Status: code authored, NOT deployed.** Deploy is a live-AWS step for the
Chunk-B session (below). Two design points are still open — see the top of
`handler.py` (the running-state handoff, and custom-domain fronting).

## What it does
On each HTTP hit (via a Function URL): checks the target instance's state →
`stopped` starts it and returns an auto-refreshing holding page; `pending`/
`stopping` shows the holding page; `running` hands off to `APP_URL`.

## Environment
| Var | Required | Example |
|---|---|---|
| `TARGET_INSTANCE_ID` | yes | `i-0123456789abcdef0` |
| `APP_URL` | for handoff | `https://aiops.example.com` |
| `HOLDING_REFRESH_SEC` | no (8) | `8` |

## Least-privilege IAM (attach to the Lambda role)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": "ec2:DescribeInstances", "Resource": "*" },
    { "Effect": "Allow", "Action": "ec2:StartInstances",
      "Resource": "arn:aws:ec2:us-east-1:ACCOUNT_ID:instance/TARGET_INSTANCE_ID" }
  ]
}
```
(`DescribeInstances` cannot be resource-scoped; `StartInstances` is pinned to the
one instance. Plus the managed `AWSLambdaBasicExecutionRole` for logs.) All AWS
CLI for deploy uses `--profile aiops-operator`.

## Deploy (Chunk-B live session — held for GO)
1. `zip -j function.zip handler.py` (boto3 is in the Lambda runtime — no deps).
2. Create the role with the policy above, then the function
   (`--handler handler.handler`, Python 3.12, env vars set).
3. Create a **Function URL** (`--auth-type NONE` — it's a public front door).
4. Point the app domain at it and settle the TLS/custom-domain fronting
   (Function URLs need CloudFront/API Gateway for a branded cert — open decision).
5. Smoke test: hit the URL with the box stopped → holding page + the instance
   moves to `pending`; hit again when `running` → redirect to `APP_URL`.
