# Wake-on-visit Lambda (5c WS4)

The "wake" half of the lite tier's sleep/wake front door — no Elastic IP, so the
$2-3/mo target holds. Pairs with `aws/idle-check.sh` (the "stop when idle" half).

**Status: DEPLOYED and verified end-to-end.** The app domain (on a CDN with a
branded cert) points at a CloudFront distribution whose origin is this Lambda's
Function URL. A visit wakes the box and 302-redirects to it once it is running.

## What it does
On each HTTP hit (via a Function URL, fronted by CloudFront):

- `stopped` → `ec2:StartInstances` + a 200 auto-refreshing holding page.
- `pending` / `stopping` → the holding page (still transitioning).
- `running` → re-point the app subdomain's A record at the box's CURRENT public
  IP, then 302 the visitor to `APP_URL`.

Why the Lambda owns the DNS update: with no Elastic IP the box's public IPv4
changes on every start, so the A record has to be re-pointed each wake. The box's
DNS is on Hostinger, which does NOT allow NS-delegation of a subdomain (so a
Route53 dyn-DNS zone can't be reached publicly). Hostinger *does* allow an A
record, so this Lambda UPSERTs it directly via the Hostinger DNS REST API. The
Hostinger token lives only in this Lambda's (encrypted-at-rest) environment —
never on the internet-exposed box. This replaces the retired box-side
`aws/dyn-dns.sh`.

## Environment
| Var | Required | Example |
|---|---|---|
| `TARGET_INSTANCE_ID` | yes | `i-0123456789abcdef0` |
| `APP_URL` | yes | `https://aiops-node.example.com` (302 target once up) |
| `HOSTINGER_API_TOKEN` | yes | Bearer token for the Hostinger DNS API — **never commit** |
| `HOSTINGER_DOMAIN` | yes | the Hostinger-managed zone, e.g. `example.com` |
| `DNS_RECORD_NAME` | yes | the subdomain record to keep current, e.g. `aiops-node` |
| `DNS_TTL` | no (60) | `60` |
| `HOLDING_REFRESH_SEC` | no (8) | `8` |

Function timeout is 20s (each Hostinger call has a 10s HTTP timeout). A warm-IP
cache keeps Hostinger traffic to the minutes right after a wake, not every request.

## Least-privilege IAM (attach to the Lambda EXECUTION role)
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
one instance. Plus the managed `AWSLambdaBasicExecutionRole` for logs.) The
Hostinger token is delivered as an environment variable, not via IAM. All AWS CLI
for deploy uses `--profile aiops-operator`.

## Front door: CloudFront + OAC (AWS_IAM Function URL)
The Function URL uses `AuthType=AWS_IAM` (a public `NONE` URL is blocked at the
account level). CloudFront reaches it through Origin Access Control (OAC), which
SigV4-signs each origin request as the CloudFront service principal. Required:

1. **OAC**: `SigningProtocol=sigv4`, `SigningBehavior=always`, `OriginType=lambda`,
   attached to the Lambda origin.
2. **Origin request policy = AllViewerExceptHostHeader** (managed). It must NOT
   forward the `Host` header, or the SigV4 signature won't match the Function URL
   host. Pair it with a CachingDisabled cache policy.
3. **TWO resource-policy statements** on the function for `cloudfront.amazonaws.com`,
   scoped to the distribution. **BOTH are required** — with only the first,
   CloudFront gets `403 AccessDeniedException` even though every other setting is
   correct (see `docs/ISSUES.md` FD-006):

```bash
aws lambda add-permission --function-name <FUNCTION_NAME> \
  --statement-id AllowCloudFrontOAC \
  --action lambda:InvokeFunctionUrl \
  --principal cloudfront.amazonaws.com \
  --function-url-auth-type AWS_IAM \
  --source-arn arn:aws:cloudfront::ACCOUNT_ID:distribution/<DISTRIBUTION_ID> \
  --profile aiops-operator

aws lambda add-permission --function-name <FUNCTION_NAME> \
  --statement-id AllowCloudFrontInvokeFunction \
  --action lambda:InvokeFunction \
  --principal cloudfront.amazonaws.com \
  --source-arn arn:aws:cloudfront::ACCOUNT_ID:distribution/<DISTRIBUTION_ID> \
  --profile aiops-operator
```

> The CloudFront service principal has no identity policy, so it relies entirely
> on this resource policy. An IAM *user* can invoke with only `InvokeFunctionUrl`
> because its identity policy supplies `InvokeFunction` — which is why the missing
> statement is easy to miss. **Any terraform/IaC for this Lambda MUST encode both
> statements.**

## Deploy
1. `zip -j function.zip handler.py` (boto3 is in the Lambda runtime — no deps).
2. Create the execution role with the policy above, then the function
   (`--handler handler.handler`, Python 3.12, timeout 20s, env vars set).
3. Create a **Function URL** with `--auth-type AWS_IAM`.
4. Put CloudFront in front (OAC + the two resource-policy statements + the
   AllViewerExceptHostHeader origin request policy + CachingDisabled), then point
   the app domain's CNAME at the distribution.
5. Smoke test: with the box stopped, hit the domain → holding page + the instance
   moves to `pending`; hit again when `running` → the A record updates and you're
   302'd to `APP_URL`.
