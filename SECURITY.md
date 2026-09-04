# Security Policy

## Supported versions

Constitutional AIOps is at an early release. Security fixes land on the latest
`1.0.x` line. Please run a current version before reporting an issue.

| Version | Supported |
| ------- | --------- |
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a vulnerability

Please do not open a public issue, pull request, or discussion for a security
problem. Public disclosure before a fix exists puts every deployment at risk.

Instead, report it privately through GitHub:

1. Go to the repository's **Security** tab.
2. Choose **Report a vulnerability** (GitHub private vulnerability reporting).
3. Describe the issue with enough detail to reproduce it.

A good report includes:

- The affected component or endpoint and the version or commit.
- Steps to reproduce, or a proof of concept.
- The impact you believe it has.
- Any suggested fix, if you have one.

## What to expect

- We aim to acknowledge a report within a few days.
- We will confirm the issue, work on a fix, and keep you updated on progress.
- Once a fix is released we are happy to credit you, unless you prefer to stay
  anonymous.

## Scope notes

- This is a self-hostable system. Many security properties depend on how an
  operator configures it (for example `AUTH_REQUIRED`, the reverse proxy, TLS,
  and which action tools are enabled). Configuration hardening advice lives in
  [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
- Action tools that change infrastructure are OFF by default and are always
  gated by the constitutional validator and, where enabled, human approval.
- Reports about a deployment you do not operate should go to that deployment's
  owner, not here.

Thank you for helping keep Constitutional AIOps and its users safe.
