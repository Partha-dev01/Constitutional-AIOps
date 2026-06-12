"""
Constitutional AIOps - Password hashing (stdlib only).

scrypt password hashes in a self-describing string format:

    scrypt$<n>$<r>$<p>$<salt_hex>$<hash_hex>

so parameters can be tuned later without breaking stored hashes. Verification
recomputes with the parameters embedded in the stored string and compares in
constant time (hmac.compare_digest). Zero new dependencies — hashlib + hmac +
secrets only.
"""

import hashlib
import hmac
import secrets

# Current cost parameters for NEW hashes (RFC 7914 interactive-login profile).
_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1
_DKLEN = 32
_SALT_BYTES = 16

# Explicit memory ceiling for scrypt (n=16384, r=8 needs ~16 MiB; leave headroom
# instead of relying on the OpenSSL default, which varies across builds).
_MAXMEM = 64 * 1024 * 1024

# Upper bounds when verifying a STORED hash, so a tampered users.db row cannot
# turn verification into a memory/CPU DoS.
_MAX_N = 1 << 20
_MAX_R = 32
_MAX_P = 16

# Password policy
MIN_PASSWORD_LENGTH = 10


def hash_password(password: str) -> str:
    """Hash a password with scrypt and a fresh random salt."""
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        maxmem=_MAXMEM,
        dklen=_DKLEN,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored self-describing scrypt hash.

    Returns False (never raises) for malformed/unknown hash strings.
    """
    if not isinstance(password, str) or not isinstance(stored, str):
        return False
    parts = stored.split("$")
    if len(parts) != 6 or parts[0] != "scrypt":
        return False
    try:
        n = int(parts[1])
        r = int(parts[2])
        p = int(parts[3])
        salt = bytes.fromhex(parts[4])
        expected = bytes.fromhex(parts[5])
    except ValueError:
        return False
    # Sanity bounds: n must be a power of two > 1; refuse hostile parameters.
    if n < 2 or n > _MAX_N or (n & (n - 1)) != 0:
        return False
    if not (1 <= r <= _MAX_R) or not (1 <= p <= _MAX_P):
        return False
    if not salt or not expected:
        return False
    try:
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            maxmem=_MAXMEM,
            dklen=len(expected),
        )
    except (ValueError, MemoryError):
        return False
    return hmac.compare_digest(derived, expected)


def validate_password_policy(password: str, username: str = "") -> None:
    """Raise ValueError when the password violates the policy.

    Policy: at least MIN_PASSWORD_LENGTH characters and not equal to the
    username (case-insensitive).
    """
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
        )
    if username and password.strip().lower() == username.strip().lower():
        raise ValueError("Password must not be the same as the username")


__all__ = [
    "MIN_PASSWORD_LENGTH",
    "hash_password",
    "validate_password_policy",
    "verify_password",
]
