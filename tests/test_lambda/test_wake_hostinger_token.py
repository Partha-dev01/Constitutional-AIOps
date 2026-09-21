"""M4: the Hostinger API token resolves from SSM, not from a plaintext env var.

The token used to live in `HOSTINGER_API_TOKEN` on the function, readable by
anyone holding `lambda:GetFunction`. It now prefers an SSM SecureString named by
`HOSTINGER_TOKEN_SSM_PARAM`.

The property that matters most here is NOT that SSM is used. It is that every
failure mode still degrades softly, because this code path is the front door: a
DNS sync that does not happen leaves the visitor on the holding page with a
manual continue, while an exception would break `/launch` outright.
"""

import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest

_HANDLER_PATH = (
    Path(__file__).resolve().parents[2] / "aws" / "lambda" / "wake_on_visit" / "handler.py"
)

_ENV_KEYS = (
    "HOSTINGER_TOKEN_SSM_PARAM",
    "HOSTINGER_API_TOKEN",
    "HOSTINGER_DOMAIN",
    "DNS_RECORD_NAME",
    "TARGET_INSTANCE_ID",
)


class FakeSsm:
    """Stand-in for the boto3 SSM client. Counts calls so caching is testable."""

    def __init__(self, value="ssm-token", error=None):
        self.value = value
        self.error = error
        self.calls = []

    def get_parameter(self, Name, WithDecryption=False):  # noqa: N803 - boto3 kwargs
        self.calls.append((Name, WithDecryption))
        if self.error is not None:
            raise self.error
        return {"Parameter": {"Value": self.value}}


def _load(**env):
    """Import the handler fresh with a specific environment and a stub boto3."""
    saved_env = {k: os.environ.get(k) for k in _ENV_KEYS}
    for k in _ENV_KEYS:
        os.environ.pop(k, None)
    os.environ["TARGET_INSTANCE_ID"] = "i-testtoken000000000"
    os.environ.update({k: v for k, v in env.items() if v is not None})

    stub = types.ModuleType("boto3")
    stub.client = lambda *a, **k: None  # tests set _ssm / _ec2 directly
    saved_boto = sys.modules.get("boto3")
    sys.modules["boto3"] = stub
    try:
        spec = importlib.util.spec_from_file_location("wake_token_under_test", _HANDLER_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if saved_boto is not None:
            sys.modules["boto3"] = saved_boto
        else:
            sys.modules.pop("boto3", None)
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return mod


# --------------------------------------------------------------------------
# resolution order
# --------------------------------------------------------------------------

def test_ssm_parameter_is_preferred_over_the_env_var():
    mod = _load(HOSTINGER_TOKEN_SSM_PARAM="/aiops/hostinger/api_token",
                HOSTINGER_API_TOKEN="legacy-env-token")
    mod._ssm = FakeSsm(value="ssm-token")
    assert mod._hostinger_token() == "ssm-token"


def test_secure_string_is_requested_decrypted():
    mod = _load(HOSTINGER_TOKEN_SSM_PARAM="/aiops/hostinger/api_token")
    fake = FakeSsm()
    mod._ssm = fake
    mod._hostinger_token()
    assert fake.calls == [("/aiops/hostinger/api_token", True)]


def test_env_var_still_works_when_no_parameter_is_configured():
    """Backwards compatible: a self-hoster without SSM keeps working."""
    mod = _load(HOSTINGER_API_TOKEN="legacy-env-token")
    mod._ssm = FakeSsm(error=AssertionError("SSM must not be called"))
    assert mod._hostinger_token() == "legacy-env-token"


# --------------------------------------------------------------------------
# laziness and caching
# --------------------------------------------------------------------------

def test_import_does_not_touch_ssm():
    """Cold import must not need AWS. The client is built on first use."""
    mod = _load(HOSTINGER_TOKEN_SSM_PARAM="/aiops/hostinger/api_token")
    assert mod._ssm is None
    assert mod._HOSTINGER_TOKEN_CACHE is None


def test_token_is_fetched_once_per_execution_context():
    mod = _load(HOSTINGER_TOKEN_SSM_PARAM="/aiops/hostinger/api_token")
    fake = FakeSsm()
    mod._ssm = fake
    for _ in range(5):
        mod._hostinger_token()
    assert len(fake.calls) == 1, "warm invocations must reuse the cached token"


def test_a_failed_read_is_not_cached_and_is_retried():
    """A transient SSM error must not be remembered as 'there is no token'."""
    mod = _load(HOSTINGER_TOKEN_SSM_PARAM="/aiops/hostinger/api_token")
    fake = FakeSsm(error=RuntimeError("throttled"))
    mod._ssm = fake
    assert mod._hostinger_token() == ""
    fake.error = None
    assert mod._hostinger_token() == "ssm-token"
    assert len(fake.calls) == 2


# --------------------------------------------------------------------------
# failure modes must degrade softly
# --------------------------------------------------------------------------

def test_ssm_failure_falls_back_to_the_env_var():
    mod = _load(HOSTINGER_TOKEN_SSM_PARAM="/aiops/hostinger/api_token",
                HOSTINGER_API_TOKEN="legacy-env-token")
    mod._ssm = FakeSsm(error=RuntimeError("AccessDeniedException"))
    assert mod._hostinger_token() == "legacy-env-token"


def test_empty_parameter_falls_back_to_the_env_var():
    mod = _load(HOSTINGER_TOKEN_SSM_PARAM="/aiops/hostinger/api_token",
                HOSTINGER_API_TOKEN="legacy-env-token")
    mod._ssm = FakeSsm(value="")
    assert mod._hostinger_token() == "legacy-env-token"


def test_no_token_anywhere_returns_empty_rather_than_raising():
    mod = _load(HOSTINGER_TOKEN_SSM_PARAM="/aiops/hostinger/api_token")
    mod._ssm = FakeSsm(error=RuntimeError("boom"))
    assert mod._hostinger_token() == ""


def test_sync_dns_skips_instead_of_raising_when_the_token_is_unavailable():
    """The whole point: a missing token degrades the wake, it does not break it."""
    mod = _load(HOSTINGER_TOKEN_SSM_PARAM="/aiops/hostinger/api_token",
                HOSTINGER_DOMAIN="example.com", DNS_RECORD_NAME="app")
    mod._ssm = FakeSsm(error=RuntimeError("AccessDeniedException"))
    assert mod._sync_dns("203.0.113.7") is False


def test_the_token_value_is_never_logged(capsys):
    mod = _load(HOSTINGER_TOKEN_SSM_PARAM="/aiops/hostinger/api_token",
                HOSTINGER_API_TOKEN="super-secret-value")
    mod._ssm = FakeSsm(error=RuntimeError("AccessDeniedException"))
    mod._hostinger_token()
    out = capsys.readouterr()
    assert "super-secret-value" not in (out.out + out.err)
    assert "/aiops/hostinger/api_token" in out.out
