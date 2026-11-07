"""Base58 (Bitcoin alphabet) encode and decode, standard library only.

The alphabet and the leading-zero convention are copied from the frontend's
`lib/solana.ts::toBase58`, because that is what the verification endpoint has to
decode. Getting the alphabet or the endianness wrong would make every signature
check fail without an obvious error, so `tests/test_base58.py` checks this
implementation against vectors produced by the frontend's own function under
node, not merely against itself.
"""

from __future__ import annotations

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_INDEX = {character: value for value, character in enumerate(ALPHABET)}


class Base58Error(ValueError):
    """Raised when a string is not valid base58."""


def encode(data: bytes) -> str:
    """Encode bytes big-endian, each leading zero byte becoming a leading '1'."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("encode expects bytes")
    if not data:
        return ""
    zeros = 0
    while zeros < len(data) and data[zeros] == 0:
        zeros += 1
    digits: list[int] = []
    for byte in data[zeros:]:
        carry = byte
        for position in range(len(digits)):
            carry += digits[position] << 8
            digits[position] = carry % 58
            carry //= 58
        while carry > 0:
            digits.append(carry % 58)
            carry //= 58
    return "1" * zeros + "".join(ALPHABET[digit] for digit in reversed(digits))


def decode(text: str) -> bytes:
    """Decode base58 to bytes. Raises Base58Error on any character not in the alphabet."""
    if not isinstance(text, str):
        raise TypeError("decode expects str")
    if text == "":
        return b""
    zeros = 0
    while zeros < len(text) and text[zeros] == "1":
        zeros += 1
    accumulator = 0
    for character in text:
        try:
            value = _INDEX[character]
        except KeyError as exc:
            raise Base58Error(f"not a base58 character: {character!r}") from exc
        accumulator = accumulator * 58 + value
    body = accumulator.to_bytes((accumulator.bit_length() + 7) // 8, "big") if accumulator else b""
    return b"\x00" * zeros + body


def looks_like_base58(text: str) -> bool:
    """True when every character is in the alphabet. Says nothing about length."""
    return bool(text) and all(character in _INDEX for character in text)
