"""Base58 against the frontend's own encoder, run under node when the vectors were made.

The expected strings below were produced by `lib/solana.ts::toBase58` (copied
verbatim into a node one-liner) rather than by this implementation, so a wrong
alphabet or a wrong leading-zero convention fails here instead of failing every
signature check in production.
"""

from __future__ import annotations

import unittest

from ticketpath.core import base58


class TestBase58(unittest.TestCase):
    def test_vectors_produced_by_the_frontend_encoder(self) -> None:
        cases = [
            (b"", ""),
            (b"\x00", "1"),
            (b"\x00\x00\x01", "112"),
            (bytes([1, 2, 3, 4, 5]), "7bWpTW"),
            (
                bytes([(index * 7 + 3) % 256 for index in range(32)]),
                "Cs8KY3PiWrCMAytMsBRQo8EdGbticVtdvufLnb2UhXh",
            ),
            (
                bytes([(index * 11 + 5) % 256 for index in range(64)]),
                "6sWzYkfjgMzEyjxmZdkyfV94EpFMgwbDbK3UUf9kaKdEmLSBCTJ7TK7mmsMYkV4DEuAksnmf9WycdqPCg7oKaZf",
            ),
            (b"\x00" * 32, "1" * 32),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw.hex()):
                self.assertEqual(base58.encode(raw), expected)
                self.assertEqual(base58.decode(expected), raw)

    def test_round_trip_for_every_length_up_to_64(self) -> None:
        for length in range(0, 65):
            raw = bytes((index * 37 + length * 11) % 256 for index in range(length))
            self.assertEqual(base58.decode(base58.encode(raw)), raw)

    def test_rejects_characters_outside_the_alphabet(self) -> None:
        for bad in ("0", "O", "I", "l", "+", "FXTURE-1"):
            with self.subTest(bad=bad):
                with self.assertRaises(base58.Base58Error):
                    base58.decode(bad)

    def test_looks_like_base58(self) -> None:
        self.assertTrue(base58.looks_like_base58("FXTUREacct111111111111111111111111111111111"))
        self.assertFalse(base58.looks_like_base58("FXTUREw1AAAAAAAAAAAAAAAAAAAAAAAAAAAl"))
        self.assertFalse(base58.looks_like_base58(""))


if __name__ == "__main__":
    unittest.main()
