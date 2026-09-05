"""
Tests for src/auth/crypto.py — at-rest secret encryption (Fernet).

Each test pins AUTH_SECRET_KEY + AIOPS_DATA_DIR (tmp) via monkeypatch and
resets the module's cached Fernet, so the derived key is rebuilt per case and
no state leaks between tests. Encryption-specific assertions skip when the
``cryptography`` dependency is absent; the empty/legacy-plaintext behavior is
verified either way (it is dependency-free).
"""

import pytest

from src.auth import crypto

_PREFIX = "enc::v1::"


@pytest.fixture
def crypto_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-crypto")
    crypto.reset_cache()
    yield tmp_path
    crypto.reset_cache()


requires_crypto = pytest.mark.skipif(
    not crypto.is_available(), reason="cryptography not installed"
)


class TestRoundTrip:
    @requires_crypto
    def test_encrypt_then_decrypt(self, crypto_env):
        secret = "sk-super-secret-byok-key-123"
        stored = crypto.encrypt_secret(secret)
        assert stored != secret
        assert stored.startswith(_PREFIX)
        assert crypto.is_encrypted(stored)
        assert crypto.decrypt_secret(stored) == secret

    @requires_crypto
    def test_ciphertext_is_nondeterministic(self, crypto_env):
        # Fernet embeds a random IV + timestamp, so two encrypts of the same
        # plaintext differ but both decrypt back to it.
        a = crypto.encrypt_secret("same-secret")
        b = crypto.encrypt_secret("same-secret")
        assert a != b
        assert crypto.decrypt_secret(a) == "same-secret"
        assert crypto.decrypt_secret(b) == "same-secret"

    @requires_crypto
    def test_unicode_secret(self, crypto_env):
        secret = "cle-tres-secrete-\U0001f510"
        assert crypto.decrypt_secret(crypto.encrypt_secret(secret)) == secret


class TestEmptyAndLegacy:
    def test_empty_roundtrips_to_empty(self, crypto_env):
        assert crypto.encrypt_secret("") == ""
        assert crypto.decrypt_secret("") == ""

    def test_legacy_plaintext_read_verbatim(self, crypto_env):
        # A value stored before this module existed has no prefix and must be
        # returned as-is (the caller re-encrypts it on the next write).
        assert not crypto.is_encrypted("sk-legacy-plaintext")
        assert crypto.decrypt_secret("sk-legacy-plaintext") == "sk-legacy-plaintext"

    def test_is_encrypted_discriminates(self, crypto_env):
        assert crypto.is_encrypted(_PREFIX + "anything")
        assert not crypto.is_encrypted("plain")
        assert not crypto.is_encrypted("")


class TestTamperAndWrongKey:
    @requires_crypto
    def test_tampered_token_returns_empty(self, crypto_env):
        stored = crypto.encrypt_secret("secret")
        body = stored[len(_PREFIX):]
        # Flip the first base64 char of the token body: any single-char change
        # fails Fernet's HMAC, so decrypt must fail closed to "" (never raise).
        tampered = _PREFIX + ("A" if body[0] != "A" else "B") + body[1:]
        assert crypto.decrypt_secret(tampered) == ""

    @requires_crypto
    def test_garbage_prefixed_token_returns_empty(self, crypto_env):
        assert crypto.decrypt_secret(_PREFIX + "not-a-real-fernet-token") == ""

    @requires_crypto
    def test_wrong_key_returns_empty(self, crypto_env, monkeypatch):
        stored = crypto.encrypt_secret("secret")
        # A different server secret derives a different Fernet key -> InvalidToken.
        monkeypatch.setenv("AUTH_SECRET_KEY", "a-totally-different-secret-key")
        crypto.reset_cache()
        assert crypto.decrypt_secret(stored) == ""


class TestAvailability:
    def test_is_available_returns_bool(self, crypto_env):
        assert isinstance(crypto.is_available(), bool)
