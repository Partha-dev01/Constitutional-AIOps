"""
Tests for src/auth/passwords.py — stdlib scrypt hashing + password policy.
"""

import pytest

from src.auth.passwords import (
    MIN_PASSWORD_LENGTH,
    hash_password,
    validate_password_policy,
    verify_password,
)


class TestHashRoundtrip:
    def test_roundtrip_verifies(self):
        stored = hash_password("correct horse battery staple")
        assert verify_password("correct horse battery staple", stored) is True

    def test_wrong_password_rejected(self):
        stored = hash_password("correct horse battery staple")
        assert verify_password("incorrect horse", stored) is False

    def test_hash_format_is_self_describing(self):
        stored = hash_password("some-password-123")
        parts = stored.split("$")
        assert len(parts) == 6
        assert parts[0] == "scrypt"
        assert parts[1] == "16384"
        assert parts[2] == "8"
        assert parts[3] == "1"
        # salt + hash are hex
        bytes.fromhex(parts[4])
        bytes.fromhex(parts[5])

    def test_distinct_salts_produce_distinct_hashes(self):
        a = hash_password("same-password-here")
        b = hash_password("same-password-here")
        assert a != b
        # ...but both verify
        assert verify_password("same-password-here", a)
        assert verify_password("same-password-here", b)


class TestMalformedHashes:
    @pytest.mark.parametrize(
        "stored",
        [
            "",
            "garbage",
            "scrypt$16384$8$1$deadbeef",  # missing hash segment
            "scrypt$16384$8$1$nothex$nothex",  # non-hex segments
            "scrypt$0$8$1$00$00",  # n too small
            "scrypt$16383$8$1$00$00",  # n not a power of two
            "bcrypt$16384$8$1$00$00",  # unknown algorithm
            "scrypt$16384$8$1$$",  # empty salt/hash
        ],
    )
    def test_malformed_hash_returns_false(self, stored):
        assert verify_password("whatever-password", stored) is False

    def test_non_string_inputs_return_false(self):
        assert verify_password(None, hash_password("good-password-1")) is False
        assert verify_password("good-password-1", None) is False


class TestPasswordPolicy:
    def test_minimum_length_enforced(self):
        with pytest.raises(ValueError):
            validate_password_policy("x" * (MIN_PASSWORD_LENGTH - 1))

    def test_minimum_length_accepted(self):
        validate_password_policy("x" * MIN_PASSWORD_LENGTH)

    def test_password_equal_to_username_rejected(self):
        with pytest.raises(ValueError):
            validate_password_policy("adminstrator", username="adminstrator")

    def test_password_equal_to_username_case_insensitive(self):
        with pytest.raises(ValueError):
            validate_password_policy("Administrator1", username="administrator1")

    def test_good_password_passes(self):
        validate_password_policy("a-long-enough-password", username="alice")
