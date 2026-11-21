"""Password hashing helpers (scrypt from the standard library, no extra packages)."""

import hashlib
import hmac
import os

# scrypt cost settings. Higher n = slower to brute-force (and slower to log in).
_N, _R, _P = 2**14, 8, 1


def hash_password(password: str) -> str:
    """Return "salt:digest" (both hex) for storing in User.password_hash."""
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return salt.hex() + ":" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    """Check a plain password against a value made by hash_password."""
    try:
        salt_hex, digest_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return hmac.compare_digest(digest.hex(), digest_hex)
