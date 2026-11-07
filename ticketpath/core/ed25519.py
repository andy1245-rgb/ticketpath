"""Ed25519 signature verification, RFC 8032, pure Python standard library.

Why this file exists: the contract's wallet-verification endpoint has to check a
base58 detached Ed25519 signature. There is no pip on this machine and no
`nacl` or `cryptography` module in the standard library, so the ~70 lines of
RFC 8032 verification are implemented here rather than pretending to verify.

`sign()` is included only so the test suite can prove `verify()` against the
RFC's published test vectors by reproducing the published signatures. The server
never calls it, it takes a raw 32-byte seed, and no key material from this
programme is stored anywhere.

Not constant-time. It verifies public data (a signature over a public message
against a public key), so timing does not leak a secret here.
"""

from __future__ import annotations

import hashlib

# Curve constants, RFC 8032 section 5.1.
_P = 2**255 - 19
_Q = 2**252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_I = pow(2, (_P - 1) // 4, _P)

# Extended homogeneous coordinates (X, Y, Z, T) with x = X/Z, y = Y/Z, xy = T/Z.


def _inv(value: int) -> int:
    return pow(value, _P - 2, _P)


def _add(first: tuple[int, int, int, int], second: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Unified point addition, RFC 8032 section 5.1.4."""
    x1, y1, z1, t1 = first
    x2, y2, z2, t2 = second
    a = (y1 - x1) * (y2 - x2) % _P
    b = (y1 + x1) * (y2 + x2) % _P
    c = t1 * 2 * _D * t2 % _P
    d = z1 * 2 * z2 % _P
    e = b - a
    f = d - c
    g = d + c
    h = b + a
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _multiply(scalar: int, point: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    result = (0, 1, 1, 0)
    addend = point
    while scalar > 0:
        if scalar & 1:
            result = _add(result, addend)
        addend = _add(addend, addend)
        scalar >>= 1
    return result


def _recover_x(y: int, sign: int) -> int | None:
    if y >= _P:
        return None
    x_squared = (y * y - 1) * _inv(_D * y * y + 1) % _P
    x = pow(x_squared, (_P + 3) // 8, _P)
    if (x * x - x_squared) % _P != 0:
        x = x * _I % _P
    if (x * x - x_squared) % _P != 0:
        return None
    if x == 0 and sign:
        return None
    if x & 1 != sign:
        x = _P - x
    return x


def _decompress(data: bytes) -> tuple[int, int, int, int] | None:
    if len(data) != 32:
        return None
    y = int.from_bytes(data, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % _P)


def _compress(point: tuple[int, int, int, int]) -> bytes:
    x, y, z, _ = point
    z_inverse = _inv(z)
    x = x * z_inverse % _P
    y = y * z_inverse % _P
    out = bytearray(y.to_bytes(32, "little"))
    out[31] |= (x & 1) << 7
    return bytes(out)


_BY = 4 * _inv(5) % _P
_BX = _recover_x(_BY, 0)
if _BX is None:  # pragma: no cover - a broken constant would fail every test
    raise RuntimeError("Ed25519 base point is not on the curve")
_BASE = (_BX, _BY, 1, _BX * _BY % _P)


def _points_equal(first: tuple[int, int, int, int], second: tuple[int, int, int, int]) -> bool:
    x1, y1, z1, _ = first
    x2, y2, z2, _ = second
    return (x1 * z2 - x2 * z1) % _P == 0 and (y1 * z2 - y2 * z1) % _P == 0


def verify(public_key: bytes, signature: bytes, message: bytes) -> bool:
    """True when `signature` is a valid detached Ed25519 signature of `message`."""
    if len(public_key) != 32 or len(signature) != 64:
        return False
    r_bytes = signature[:32]
    s = int.from_bytes(signature[32:], "little")
    if s >= _Q:
        return False
    public_point = _decompress(public_key)
    r_point = _decompress(r_bytes)
    if public_point is None or r_point is None:
        return False
    challenge = int.from_bytes(
        hashlib.sha512(r_bytes + public_key + message).digest(), "little"
    ) % _Q
    return _points_equal(
        _multiply(s, _BASE),
        _add(r_point, _multiply(challenge, public_point)),
    )


def sign(seed: bytes, message: bytes) -> tuple[bytes, bytes]:
    """Test support only: derive (public_key, signature) from a 32-byte seed.

    The server never calls this. It exists so `tests/test_ed25519.py` can prove
    the verifier against RFC 8032's published vectors, where the expected
    signature is known and must be reproduced byte for byte.
    """
    if len(seed) != 32:
        raise ValueError("seed must be 32 bytes")
    digest = hashlib.sha512(seed).digest()
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    prefix = digest[32:]
    public_key = _compress(_multiply(scalar, _BASE))
    nonce = int.from_bytes(hashlib.sha512(prefix + message).digest(), "little") % _Q
    r_bytes = _compress(_multiply(nonce, _BASE))
    challenge = int.from_bytes(
        hashlib.sha512(r_bytes + public_key + message).digest(), "little"
    ) % _Q
    s = (nonce + challenge * scalar) % _Q
    return public_key, r_bytes + s.to_bytes(32, "little")
