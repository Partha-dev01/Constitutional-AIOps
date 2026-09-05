"""
Constitutional AIOps - at-rest secret encryption (Fernet).

Encrypts small secrets (today: a bring-your-own LLM API key) BEFORE they are
written to disk in ``settings.json`` / the ``user_settings`` table. The Fernet
key is derived from the server secret that already signs sessions
(``AUTH_SECRET_KEY`` env, else the generated key file — see
``src.auth.tokens._get_secret``) via HKDF-SHA256, so:

  * no new key material has to be provisioned or rotated separately, and
  * the ciphertext decrypts across restarts and by any worker that shares the
    same server secret.

Stored form:  ``"enc::v1::<fernet-token>"``. A value WITHOUT that prefix is
read back verbatim (LEGACY PLAINTEXT), so a key stored before this module
existed keeps working and is transparently re-encrypted on the next write.
``decrypt_secret`` NEVER raises: a tampered / wrong-key token logs a warning
and returns ``""``.

If the ``cryptography`` package is somehow unavailable (a stripped dev image),
encryption degrades to a clearly-warned PASSTHROUGH that stores plaintext —
matching the pre-encryption behavior rather than blocking boot. Production
ships the dependency (``requirements.txt``), so real encryption is active
there.
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Stored-form marker. Bump the version segment only alongside a deliberate,
# migration-aware key/format change.
_PREFIX = "enc::v1::"

# Fixed, non-secret HKDF parameters. The server secret is already high-entropy,
# so a CONSTANT salt is correct here: the derived key must be identical across
# restarts to decrypt what an earlier process wrote. Changing ``_HKDF_INFO``
# intentionally rotates the derived key (old ciphertexts then fail closed).
_HKDF_SALT = b"aiops-byok-atrest-v1"
_HKDF_INFO = b"aiops-secret-encryption-key"

try:  # cryptography is an explicit dependency; degrade gracefully if absent.
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    _CRYPTO_AVAILABLE = True
except Exception:  # noqa: BLE001 - any import failure => passthrough mode
    _CRYPTO_AVAILABLE = False

_fernet_cache: "Optional[Fernet]" = None
_warned_passthrough = False


def is_available() -> bool:
    """True when real encryption is active (the ``cryptography`` dep imported)."""
    return _CRYPTO_AVAILABLE


def reset_cache() -> None:
    """Drop the cached Fernet.

    Only needed by tests that monkeypatch the server secret between cases; the
    next encrypt/decrypt rebuilds the key from the current secret.
    """
    global _fernet_cache
    _fernet_cache = None


def is_encrypted(value: str) -> bool:
    """True when ``value`` is in this module's encrypted stored form."""
    return isinstance(value, str) and value.startswith(_PREFIX)


def _fernet() -> "Fernet":
    """Build (and cache) the Fernet from the HKDF-derived server key."""
    global _fernet_cache
    if _fernet_cache is None:
        # Lazy import avoids any import-time coupling to the token module.
        from src.auth.tokens import _get_secret

        derived = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_HKDF_SALT,
            info=_HKDF_INFO,
        ).derive(_get_secret())
        _fernet_cache = Fernet(base64.urlsafe_b64encode(derived))
    return _fernet_cache


def encrypt_secret(plaintext: str) -> str:
    """Return the stored form of a secret.

    Empty in => empty out, so a ``…KeySet`` boolean derived from the stored
    value stays correct. When ``cryptography`` is unavailable the plaintext is
    returned unchanged with a one-time warning (matching prior behavior).
    """
    if not plaintext:
        return ""
    if not _CRYPTO_AVAILABLE:
        global _warned_passthrough
        if not _warned_passthrough:
            logger.warning(
                "cryptography not installed; storing secrets WITHOUT encryption. "
                "Install the 'cryptography' dependency for at-rest encryption."
            )
            _warned_passthrough = True
        return plaintext
    try:
        token = _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")
        return _PREFIX + token
    except Exception as exc:  # noqa: BLE001 - never block a save on a crypto error
        logger.error(
            "Secret encryption failed (%s); storing plaintext", type(exc).__name__
        )
        return plaintext


def decrypt_secret(stored: str) -> str:
    """Return the plaintext for a stored secret (NEVER raises).

    Three cases: empty => ``""``; the ``enc::v1::`` prefix => Fernet-decrypt (a
    tampered / wrong-key token logs and returns ``""``); anything else =>
    LEGACY PLAINTEXT returned verbatim so pre-encryption values keep working.
    """
    if not stored:
        return ""
    if not is_encrypted(stored):
        return stored  # legacy plaintext (upgraded to ciphertext on next write)
    if not _CRYPTO_AVAILABLE:
        logger.error(
            "Encrypted secret found but 'cryptography' is unavailable; ignoring it."
        )
        return ""
    token = stored[len(_PREFIX):]
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        logger.warning(
            "Stored secret failed to decrypt (tampered or wrong key); ignoring it."
        )
        return ""
    except Exception as exc:  # noqa: BLE001 - a decrypt must never crash a request
        logger.warning(
            "Stored secret decrypt error (%s); ignoring it.", type(exc).__name__
        )
        return ""


__all__ = [
    "decrypt_secret",
    "encrypt_secret",
    "is_available",
    "is_encrypted",
    "reset_cache",
]
