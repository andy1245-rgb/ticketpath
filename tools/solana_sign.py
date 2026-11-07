"""Sign one Solana transaction message and print nothing but the signature.

`tools/devnet_publish.py` never opens the devnet keypair. It builds the bytes, hands them to
this process, and gets back 64 bytes of signature. That separation is the point: the publish
script has no line that reads key material, so no print, log line or traceback in it can leak
a byte of it, and this file's whole surface is "read a seed, sign, print a signature".

    TP_DEVNET_KEYPAIR=~/.config/ticketpath-devnet/authority.json \
        python3 tools/solana_sign.py < message.bin > signature.base58

Reads the message on stdin as raw bytes (or `--base64` for base64). Writes the base58
signature and a newline on stdout. Everything else -- including a warning about file
permissions -- goes to stderr, and never contains key bytes.

Why not shell out to `solana-keygen`? It has no "sign this message" verb: `new`, `pubkey`,
`recover`, `grind`, `verify` and `bls_pubkey` are the whole set, and `solana
sign-offchain-message` wraps the bytes in an off-chain-message header, so its signature is not
a transaction signature. The three instructions this repository has to send that `solana` and
`spl-token` cannot express are therefore signed here, with the RFC 8032 implementation the
test suite already proves against the published vectors (`ticketpath/core/ed25519.py`).

Not constant-time, and it does not need to be: it runs once per transaction on a machine that
holds the key anyway. It is not a general-purpose tool -- it signs, it prints, it exits.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ticketpath.core import base58, ed25519  # noqa: E402

DEFAULT_KEYPAIR = "~/.config/ticketpath-devnet/authority.json"


def keypair_path(explicit: str | None) -> Path:
    raw = explicit or os.environ.get("TP_DEVNET_KEYPAIR") or DEFAULT_KEYPAIR
    return Path(raw).expanduser()


def _warn(message: str) -> None:
    sys.stderr.write(f"solana_sign: {message}\n")
    sys.stderr.flush()


def load_seed_and_public(path: Path) -> tuple[bytes, bytes]:
    """The 32-byte seed and the public key a Solana keypair file holds, and no copy of it."""
    if not path.exists():
        raise SystemExit(f"solana_sign: no keypair at {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        _warn(f"{path} is mode {mode:04o}; 0600 is the only mode a keypair should have")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # The exception text of a JSON decode can quote the document. Never let it through.
        raise SystemExit(f"solana_sign: {path} is not readable as a keypair ({type(exc).__name__})") from None
    if not isinstance(raw, list) or len(raw) != 64 or not all(isinstance(v, int) and 0 <= v < 256 for v in raw):
        raise SystemExit(f"solana_sign: {path} is not the 64-integer shape a Solana keypair has")
    seed = bytes(raw[:32])
    stored_public = bytes(raw[32:])
    derived_public, _ = ed25519.sign(seed, b"")
    if derived_public != stored_public:
        raise SystemExit(f"solana_sign: {path} is corrupt: the public half does not match the seed")
    return seed, stored_public


def sign_message(seed: bytes, public_key: bytes, message: bytes) -> bytes:
    """One RFC 8032 signature, checked against the verifier before it is returned."""
    derived_public, signature = ed25519.sign(seed, message)
    if derived_public != public_key:
        raise SystemExit("solana_sign: the keypair's public half does not match its seed")
    if not ed25519.verify(public_key, signature, message):
        raise SystemExit("solana_sign: the signature it just made does not verify; refusing to print it")
    return signature


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/solana_sign.py", description="sign one message, print one signature")
    parser.add_argument("--keypair", help=f"keypair path (default $TP_DEVNET_KEYPAIR or {DEFAULT_KEYPAIR})")
    parser.add_argument("--base64", action="store_true", help="the message on stdin is base64, not raw")
    parser.add_argument("--public-key", action="store_true", help="print the public key instead of signing")
    args = parser.parse_args(argv)

    path = keypair_path(args.keypair)
    seed, public_key = load_seed_and_public(path)

    if args.public_key:
        sys.stdout.write(base58.encode(public_key) + "\n")
        return 0

    message = sys.stdin.buffer.read()
    if args.base64:
        try:
            message = base64.b64decode(message.strip(), validate=True)
        except ValueError:
            raise SystemExit("solana_sign: stdin is not base64") from None
    if not message:
        raise SystemExit("solana_sign: no message on stdin")

    sys.stdout.write(base58.encode(sign_message(seed, public_key, message)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
