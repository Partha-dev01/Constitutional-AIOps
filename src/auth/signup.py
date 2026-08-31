"""
Constitutional AIOps - Public self-service signup helpers (stdlib only).

Public signup is a HOSTED-demo feature and is OFF by default so a self-host
deployment keeps the minimal admin-managed attack surface. Enable it with
``AIOPS_ENABLE_PUBLIC_SIGNUP=true`` on the hosted instance only.

Abuse controls layered on top of the store's password policy + the route's
per-IP throttle:
  * CAPTCHA  - Cloudflare Turnstile or hCaptcha (server-side siteverify).
  * Email    - a signed, expiring verification link is emailed via SMTP
               (works with the Amazon SES SMTP endpoint); the account is
               usable immediately (shared demo) and the link flips a soft
               ``email_verified`` flag. This sidesteps the sleeping-box wrinkle
               (a later click need not find the app awake to create the account).

Everything here is stdlib: urllib for the captcha siteverify call, smtplib for
mail. No new dependencies, no boto3.

Relevant environment (all optional; unset = feature effectively disabled/dev):
  AIOPS_ENABLE_PUBLIC_SIGNUP   master flag (default false)
  SIGNUP_CAPTCHA_PROVIDER      "turnstile" | "hcaptcha" | "" (none)
  SIGNUP_CAPTCHA_SITE_KEY      public site key (exposed to the SPA)
  SIGNUP_CAPTCHA_SECRET        server secret for siteverify
  SIGNUP_SMTP_HOST/PORT/USER/PASSWORD, SIGNUP_EMAIL_FROM   SES SMTP creds
  PUBLIC_BASE_URL              e.g. https://aiops-node.example.com (verify links)
"""

import json
import logging
import os
import re
import smtplib
import ssl
import urllib.parse
import urllib.request
from email.message import EmailMessage
from typing import Optional

from src.auth import tokens

logger = logging.getLogger(__name__)

_TRUTHY = {"1", "true", "yes", "on"}

# RFC-5322-lite: good enough to reject obvious garbage without over-rejecting.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_CAPTCHA_VERIFY_URLS = {
    "turnstile": "https://challenges.cloudflare.com/turnstile/v0/siteverify",
    "hcaptcha": "https://hcaptcha.com/siteverify",
}

_VERIFY_PURPOSE = "email_verify"
_VERIFY_TTL_SECONDS = 3 * 24 * 60 * 60  # 3 days


def signup_enabled() -> bool:
    return os.environ.get("AIOPS_ENABLE_PUBLIC_SIGNUP", "").strip().lower() in _TRUTHY


def captcha_provider() -> str:
    provider = os.environ.get("SIGNUP_CAPTCHA_PROVIDER", "").strip().lower()
    return provider if provider in _CAPTCHA_VERIFY_URLS else ""


def captcha_site_key() -> str:
    """Public site key for the SPA widget (safe to expose)."""
    return os.environ.get("SIGNUP_CAPTCHA_SITE_KEY", "").strip()


def public_config() -> dict[str, object]:
    """The signup-related fields the public /auth/config endpoint returns."""
    provider = captcha_provider()
    return {
        "signup_enabled": signup_enabled(),
        "captcha_provider": provider,
        "captcha_site_key": captcha_site_key() if provider else "",
    }


def is_valid_email(email: str) -> bool:
    email = (email or "").strip()
    return bool(email) and len(email) <= 254 and _EMAIL_RE.match(email) is not None


def verify_captcha(token: str, remote_ip: str = "") -> bool:
    """Server-side captcha check. Fail-closed when a provider is configured.

    * No provider configured  -> True  (captcha disabled; dev / behind other controls).
    * Provider but no secret   -> False (misconfiguration must not open a hole).
    * Provider + secret        -> POST siteverify; True only on {"success": true}.
    """
    provider = captcha_provider()
    if not provider:
        return True
    secret = os.environ.get("SIGNUP_CAPTCHA_SECRET", "").strip()
    if not secret:
        logger.error("captcha provider %s set but SIGNUP_CAPTCHA_SECRET is empty", provider)
        return False
    if not token:
        return False
    data = urllib.parse.urlencode(
        {"secret": secret, "response": token, "remoteip": remote_ip or ""}
    ).encode("utf-8")
    req = urllib.request.Request(_CAPTCHA_VERIFY_URLS[provider], data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return bool(result.get("success"))
    except Exception as exc:  # noqa: BLE001 - any failure => not verified
        logger.warning("captcha siteverify (%s) failed: %s", provider, exc)
        return False


def make_verify_token(user_id: str, email: str) -> str:
    return tokens.sign_value(
        {"purpose": _VERIFY_PURPOSE, "sub": user_id, "email": email},
        _VERIFY_TTL_SECONDS,
    )


def read_verify_token(token: str) -> Optional[dict]:
    """Return the claims of a valid, unexpired email-verify token, else None."""
    claims = tokens.read_value(token)
    if not claims or claims.get("purpose") != _VERIFY_PURPOSE:
        return None
    if not isinstance(claims.get("sub"), str):
        return None
    return claims


def _verify_url(token: str) -> str:
    base = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    path = "/api/v1/auth/verify?token=" + urllib.parse.quote(token, safe="")
    return f"{base}{path}" if base else path


def send_verification_email(to_addr: str, token: str) -> bool:
    """Email the verification link. Best-effort: never raises.

    With no SMTP host configured (local/dev) the link is logged and True is
    returned so signup still succeeds; the account is usable regardless.
    """
    verify_url = _verify_url(token)
    host = os.environ.get("SIGNUP_SMTP_HOST", "").strip()
    from_addr = os.environ.get("SIGNUP_EMAIL_FROM", "").strip() or "no-reply@localhost"
    if not host:
        logger.info("signup: no SMTP configured; verification link for %s: %s", to_addr, verify_url)
        return True

    msg = EmailMessage()
    msg["Subject"] = "Confirm your Constitutional AIOps demo account"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(
        "Welcome to the Constitutional AIOps demo.\n\n"
        "Confirm your email address by opening this link:\n"
        f"{verify_url}\n\n"
        "Your account already works; this just confirms we can reach you. "
        "The link expires in 3 days. If you did not sign up, ignore this email.\n"
    )
    port = int(os.environ.get("SIGNUP_SMTP_PORT", "587"))
    user = os.environ.get("SIGNUP_SMTP_USER", "").strip()
    password = os.environ.get("SIGNUP_SMTP_PASSWORD", "")
    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
        logger.info("signup: verification email sent to %s", to_addr)
        return True
    except Exception as exc:  # noqa: BLE001 - mail failure must not fail signup
        logger.warning("signup: verification email to %s failed: %s", to_addr, exc)
        return False


__all__ = [
    "captcha_provider",
    "captcha_site_key",
    "is_valid_email",
    "make_verify_token",
    "public_config",
    "read_verify_token",
    "send_verification_email",
    "signup_enabled",
    "verify_captcha",
]
