"""The wire contract as an executable test.

`lib/types.ts` + `API_CONTRACT.md` in the platform's own frontend checkout, a sibling
directory outside this repository (`../ticketing-frontend`), are the
acceptance test for this backend. This module turns that document into code:
every route the server serves is addressed over a real socket, and its response
is checked against a copy of the contract that is **written out here**, not
imported from the backend. A test that imports the thing it tests proves
nothing about the contract, it proves the code agrees with itself.

Nothing in this file imports `ticketpath`. The server is started as a
subprocess, the way an operator starts it.

Two layers per route:

1. Structure. Every field the contract declares must be present, of the right
   JSON type, with arrays checked element by element, nullable fields allowed to
   be null or their type (never absent), and no field name the contract does not
   define. The contract is encoded in `SCHEMAS`-style tables below, one per type,
   and `ROUTES` binds one table to each route.

2. Semantics. The rules the contract states in prose rather than in types:
   markup measured against *that ticket's own tier face* (never re-derived at
   event level), integer lamports wherever money appears, ISO-8601 UTC for every
   timestamp, the enum domains, and the null-vs-absent distinction.

Extra top-level keys: the contract defines none, so the strict reading is
"exactly these keys". A few are deliberate additions declared in
`records/CONTRACT-MAP.md` §7.2/§7.3 (`dataSource` on every payload, plus
`custodyNote` and `analyticsNote`). This test allows exactly those and fails on
any *undeclared* extra key; it also records which routes are not wire-exact, so
the strict reading stays visible instead of being quietly relaxed.

One file by requirement, laid out top to bottom so a stranger can find a layer:

    1. the type language and the contract tables (one per wire type)
    2. base58 + Ed25519, for the one route whose input must really be signed
    3. the structural validator
    4. the live server handle and HTTP client
    5. the semantics: the contract's prose, one function per route
    6. the route table
    7. the run, the unittest surface, and the printed report

Run:

    python3 tests/test_contract_conformance.py --table   # per-route report
    python3 tests/test_contract_conformance.py           # unittest, starts a server
    python3 -m unittest tests.test_contract_conformance
    TICKETPATH_BASE_URL=http://127.0.0.1:8788 python3 tests/test_contract_conformance.py --table

With `TICKETPATH_BASE_URL` unset it starts `python3 -m ticketpath.server` on the
first free port among `TICKETPATH_TEST_PORT`, 8788 and an OS-chosen port, logs
under /tmp, and kills only the process it started. Port 8787 is refused: the
fleet page owns it.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from datetime import date as _date
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESERVED_PORTS = (8787,)

# ---------------------------------------------------------------------------
# The type language. Deliberately tiny: this is a wire format, not JSON Schema.
# ---------------------------------------------------------------------------

STR = "str"
INT = "int"            # JSON integer, never a float, never a bool
BOOL = "bool"
LAMPORTS = "lamports"  # integer count of lamports, >= 0
BPS = "bps"            # signed integer basis points
ISO = "iso"            # ISO-8601 UTC instant, 'Z' or '+00:00'
DAY = "day"            # ISO-8601 calendar date, YYYY-MM-DD
WALLET = "wallet"      # 32-byte base58 public key

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|\+00:00)$")
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def nullable(spec):
    """`T | null`: the key must be present, the value may be null."""
    return ("null", spec)


def array(spec):
    return ("array", spec)


def one_of(*values):
    return ("enum", values)


def obj(schema):
    return ("object", schema)


def open_obj():
    """An object whose fields the contract does not pin down (/health only)."""
    return ("object_any",)


def share():
    """A 0-1 ratio, as the contract describes `resoldShare`."""
    return ("share",)


EVENT_STATUSES = ("draft", "on_sale", "sold_out", "completed", "cancelled")
TICKET_STATUSES = ("valid", "listed", "redeemed", "revoked")
LEDGER_KINDS = ("issue", "sale", "transfer", "redeem", "revoke")
VERIFICATION_METHODS = ("wallet_signature", "identity")

# ---------------------------------------------------------------------------
# The contract, encoded. Source: lib/types.ts + API_CONTRACT.md.
# ---------------------------------------------------------------------------

DATA_SOURCE = obj({
    "mode": STR,
    "synthetic": BOOL,
    "label": STR,
    "note": STR,
})

ORGANIZER = obj({
    "id": STR,
    "name": STR,
    "walletAddress": WALLET,
    "verified": BOOL,
})

TIER = obj({
    "id": STR,
    "name": STR,
    "faceValueLamports": LAMPORTS,
    "totalSupply": INT,
    "issuedCount": INT,
})

EVENT = obj({
    "id": STR,
    "slug": STR,
    "name": STR,
    "description": STR,
    "venue": STR,
    "city": STR,
    "startsAt": ISO,
    "endsAt": nullable(ISO),
    "imageUrl": nullable(STR),
    "organizer": ORGANIZER,
    "status": one_of(*EVENT_STATUSES),
    "tiers": array(TIER),
    "totalSupply": INT,
    "issuedCount": INT,
    "resaleEnabled": BOOL,
    "resalePriceCapBps": nullable(INT),
    "requiresVerifiedWallet": BOOL,
})

TICKET = obj({
    "id": STR,
    "eventId": STR,
    "tierId": STR,
    "mintAddress": WALLET,
    "serial": STR,
    "ownerWallet": WALLET,
    "issuedToWallet": WALLET,
    "faceValueLamports": LAMPORTS,
    "lastSalePriceLamports": nullable(LAMPORTS),
    "transferCount": INT,
    "status": one_of(*TICKET_STATUSES),
    "transferRestricted": BOOL,
    "issuedAt": ISO,
    "redeemedAt": nullable(ISO),
})

LEDGER_ENTRY = obj({
    "id": STR,
    "ticketId": STR,
    "kind": one_of(*LEDGER_KINDS),
    "fromWallet": nullable(WALLET),
    "toWallet": nullable(WALLET),
    "priceLamports": nullable(LAMPORTS),
    "markupBps": nullable(BPS),
    "signature": nullable(STR),
    "slot": nullable(INT),
    "occurredAt": ISO,
})

RESALE_STATS = obj({
    "saleCount": INT,
    "transferCount": INT,
    "avgMarkupBps": nullable(BPS),
    "peakPriceLamports": nullable(LAMPORTS),
    "lastPriceLamports": nullable(LAMPORTS),
    "totalVolumeLamports": LAMPORTS,
    "uniqueWallets": INT,
})

RESALE_HISTORY = obj({
    "ticketId": STR,
    "faceValueLamports": LAMPORTS,
    "entries": array(LEDGER_ENTRY),
    "stats": RESALE_STATS,
})

WALLET_VERIFICATION = obj({
    "wallet": WALLET,
    "verified": BOOL,
    "verifiedAt": nullable(ISO),
    "method": nullable(one_of(*VERIFICATION_METHODS)),
    "canPurchase": BOOL,
    "canReceiveTransfer": BOOL,
    "flags": array(STR),
})

CHALLENGE = obj({
    "nonce": STR,
    "expiresAt": ISO,
})

PRICE_POINT = obj({
    "date": DAY,
    "avgPriceLamports": LAMPORTS,
    "saleCount": INT,
    "avgMarkupBps": nullable(BPS),
})

MARKUP_BUCKET = obj({
    "label": STR,
    "fromBps": INT,
    "toBps": nullable(INT),
    "count": INT,
})

DESTINATION_ROW = obj({
    "wallet": WALLET,
    "ticketCount": INT,
    "region": nullable(STR),
    "acquiredOnSecondary": BOOL,
})

EVENT_ANALYTICS = obj({
    "eventId": STR,
    "faceValueLamports": LAMPORTS,
    "totalVolumeLamports": LAMPORTS,
    "saleCount": INT,
    "avgMarkupBps": nullable(BPS),
    "medianResalePriceLamports": nullable(LAMPORTS),
    "resoldShare": share(),
    "uniqueHolders": INT,
    "priceSeries": array(PRICE_POINT),
    "markupDistribution": array(MARKUP_BUCKET),
    "topDestinations": array(DESTINATION_ROW),
})

PAGE_EVENT = obj({"items": array(EVENT), "nextCursor": nullable(STR)})
PAGE_TICKET = obj({"items": array(TICKET), "nextCursor": nullable(STR)})

# API_CONTRACT.md, the markup bucket table: six rows, that order, those bounds.
# The dashes in the labels are U+2013 EN DASH in the contract, and the labels are
# the exact strings it prints, so they are written as escapes.
CONTRACT_MARKUP_BUCKETS = (
    ("At or below face", -10_000, 1),
    ("0\u201325%", 1, 2_500),
    ("25\u201350%", 2_500, 5_000),
    ("50\u2013100%", 5_000, 10_000),
    ("100\u2013200%", 10_000, 20_000),
    ("Over 200%", 20_000, None),
)


def verification_message(wallet, nonce, cluster):
    """The frozen string from API_CONTRACT.md: five lines, no trailing newline."""
    return "\n".join(
        (
            "Verify wallet ownership for ticket issuance.",
            "",
            f"Wallet: {wallet}",
            f"Nonce: {nonce}",
            f"Cluster: {cluster}",
        )
    )


# ---------------------------------------------------------------------------
# base58 + Ed25519 signing: needed to exercise the verification success path,
# the one route whose input must be cryptographically valid. Written from RFC
# 8032 here rather than borrowed from the server, and pinned to RFC test vector 1
# by TestHarnessSelfCheck so a harness bug cannot masquerade as a server bug.
# ---------------------------------------------------------------------------

_B58_INDEX = {char: index for index, char in enumerate(BASE58_ALPHABET)}


def b58decode(text):
    number = 0
    for char in text:
        if char not in _B58_INDEX:
            raise ValueError(f"{char!r} is not base58")
        number = number * 58 + _B58_INDEX[char]
    body = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    leading = len(text) - len(text.lstrip("1"))
    return b"\x00" * leading + body


def b58encode(raw):
    number = int.from_bytes(raw, "big")
    out = ""
    while number:
        number, remainder = divmod(number, 58)
        out = BASE58_ALPHABET[remainder] + out
    leading = len(raw) - len(raw.lstrip(b"\x00"))
    return "1" * leading + out


P25519 = 2**255 - 19
ORDER = 2**252 + 27742317777372353535851937790883648493
SQRT_M1 = pow(2, (P25519 - 1) // 4, P25519)
EDWARDS_D = -121665 * pow(121666, P25519 - 2, P25519) % P25519


def _invert(value):
    return pow(value, P25519 - 2, P25519)


def _recover_x(y, sign_bit):
    xx = (y * y - 1) * _invert(EDWARDS_D * y * y + 1) % P25519
    if xx == 0:
        return None if sign_bit else 0
    x = pow(xx, (P25519 + 3) // 8, P25519)
    if (x * x - xx) % P25519 != 0:
        x = x * SQRT_M1 % P25519
    if (x * x - xx) % P25519 != 0:
        return None
    if (x & 1) != sign_bit:
        x = P25519 - x
    return x


_BASE_Y = 4 * _invert(5) % P25519
_BASE = (_recover_x(_BASE_Y, 0), _BASE_Y)


def _point_add(first, second):
    x1, y1 = first
    x2, y2 = second
    k = EDWARDS_D * x1 * x2 * y1 * y2 % P25519
    return (
        (x1 * y2 + x2 * y1) * _invert(1 + k) % P25519,
        (y1 * y2 + x1 * x2) * _invert(1 - k) % P25519,
    )


def _scalar_mul(scalar, point):
    result = (0, 1)
    while scalar > 0:
        if scalar & 1:
            result = _point_add(result, point)
        point = _point_add(point, point)
        scalar >>= 1
    return result


def _encode_point(point):
    x, y = point
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _clamped_scalar(seed):
    digest = hashlib.sha512(seed).digest()
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    return scalar, digest[32:]


def ed25519_public_key(seed):
    scalar, _prefix = _clamped_scalar(seed)
    return _encode_point(_scalar_mul(scalar, _BASE))


def ed25519_sign(seed, message):
    scalar, prefix = _clamped_scalar(seed)
    public = _encode_point(_scalar_mul(scalar, _BASE))
    nonce = int.from_bytes(hashlib.sha512(prefix + message).digest(), "little") % ORDER
    commitment = _encode_point(_scalar_mul(nonce, _BASE))
    challenge = int.from_bytes(
        hashlib.sha512(commitment + public + message).digest(), "little"
    ) % ORDER
    proof = (nonce + challenge * scalar) % ORDER
    return commitment + proof.to_bytes(32, "little")


# ---------------------------------------------------------------------------
# Structural validation.
# ---------------------------------------------------------------------------

def _typename(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _parse_iso(text):
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def check_value(value, spec, path, errors):
    """Validate one node against one spec, appending readable errors."""
    if isinstance(spec, tuple):
        tag = spec[0]
        if tag == "null":
            if value is not None:
                check_value(value, spec[1], path, errors)
            return
        if tag == "array":
            if not isinstance(value, list):
                errors.append(f"{path}: expected array, got {_typename(value)}")
                return
            for index, item in enumerate(value):
                check_value(item, spec[1], f"{path}[{index}]", errors)
            return
        if tag == "enum":
            allowed = spec[1]
            if not isinstance(value, str):
                errors.append(f"{path}: expected a string from the union, got {_typename(value)}")
                return
            if value not in allowed:
                errors.append(f"{path}: {value!r} is outside the contract union {list(allowed)}")
            return
        if tag == "object":
            check_object(value, spec[1], path, None, errors)
            return
        if tag == "object_any":
            if not isinstance(value, dict):
                errors.append(f"{path}: expected object, got {_typename(value)}")
            return
        if tag == "share":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{path}: expected a number in 0..1, got {_typename(value)}")
            elif not 0.0 <= float(value) <= 1.0:
                errors.append(f"{path}: {value!r} is outside the contract range 0..1")
            return
        raise AssertionError(f"unknown spec tag {tag!r} at {path}")

    if spec in (STR, WALLET):
        if not isinstance(value, str):
            errors.append(f"{path}: expected string, got {_typename(value)}")
            return
        if spec == WALLET:
            try:
                raw = b58decode(value)
            except ValueError as exc:
                errors.append(f"{path}: {value!r} is not base58 ({exc})")
                return
            if len(raw) != 32:
                errors.append(
                    f"{path}: contract says a 32-byte base58 public key; "
                    f"{value!r} decodes to {len(raw)} bytes"
                )
        return
    if spec == INT:
        if not _is_int(value):
            errors.append(f"{path}: expected integer, got {_typename(value)} ({value!r})")
        return
    if spec == LAMPORTS:
        if not _is_int(value):
            errors.append(
                f"{path}: money must be an integer count of lamports, got "
                f"{_typename(value)} ({value!r})"
            )
        elif value < 0:
            errors.append(f"{path}: negative lamport amount {value!r}")
        return
    if spec == BPS:
        if not _is_int(value):
            errors.append(f"{path}: markup must be integer basis points, got {_typename(value)}")
        return
    if spec == BOOL:
        if not isinstance(value, bool):
            errors.append(f"{path}: expected boolean, got {_typename(value)} ({value!r})")
        return
    if spec == ISO:
        if not isinstance(value, str):
            errors.append(f"{path}: expected ISO-8601 UTC string, got {_typename(value)}")
            return
        if not ISO_RE.match(value):
            errors.append(f"{path}: {value!r} is not ISO-8601 UTC with a 'Z' or '+00:00' offset")
            return
        try:
            moment = _parse_iso(value)
        except ValueError:
            errors.append(f"{path}: {value!r} does not parse as ISO-8601")
            return
        if moment.utcoffset() is not None and moment.utcoffset().total_seconds() != 0:
            errors.append(f"{path}: {value!r} is not UTC")
        return
    if spec == DAY:
        if not isinstance(value, str):
            errors.append(f"{path}: expected YYYY-MM-DD, got {_typename(value)}")
            return
        if not DAY_RE.match(value):
            errors.append(f"{path}: {value!r} is not a YYYY-MM-DD calendar date")
            return
        try:
            _date.fromisoformat(value)
        except ValueError:
            errors.append(f"{path}: {value!r} is not a real calendar date")
        return
    raise AssertionError(f"unknown spec {spec!r} at {path}")


def check_object(node, schema, path, extra_specs, errors):
    """Exact shape: required keys present, no undeclared keys, values typed."""
    if not isinstance(node, dict):
        errors.append(f"{path}: expected object, got {_typename(node)}")
        return
    present = set(node)
    expected = set(schema)
    extra_specs = extra_specs or {}
    for missing in sorted(expected - present):
        errors.append(f"{path}.{missing}: the contract requires this field; it is absent")
    for unexpected in sorted(present - expected - set(extra_specs)):
        errors.append(f"{path}.{unexpected}: field is not defined by the contract")
    for key, spec in schema.items():
        if key in node:
            check_value(node[key], spec, f"{path}.{key}", errors)
    for key, spec in extra_specs.items():
        if key in node:
            check_value(node[key], spec, f"{path}.{key}", errors)


# ---------------------------------------------------------------------------
# Arithmetic, recomputed independently of the server. Rounding is half away from
# zero, matching the contract's worked example.
# ---------------------------------------------------------------------------

def round_half_away(numerator, denominator):
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    return sign * quotient


def markup_bps(price, face):
    return round_half_away((price - face) * 10_000, face)


def integer_mean(values):
    if not values:
        return None
    return round_half_away(sum(values), len(values))


def median_int(values):
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return round_half_away(ordered[middle - 1] + ordered[middle], 2)


def utc_day(timestamp):
    return _parse_iso(timestamp).astimezone(timezone.utc).strftime("%Y-%m-%d")


def bucket_label(markup):
    for label, from_bps, to_bps in CONTRACT_MARKUP_BUCKETS:
        if markup >= from_bps and (to_bps is None or markup < to_bps):
            return label
    return CONTRACT_MARKUP_BUCKETS[0][0]


# ---------------------------------------------------------------------------
# Live server and client.
# ---------------------------------------------------------------------------

class ServerHandle:
    """Owns the process it starts, and nothing else.

    With TICKETPATH_BASE_URL set, no process is started and none is killed.
    """

    def __init__(self):
        self.base_url = os.environ.get("TICKETPATH_BASE_URL", "").rstrip("/")
        self.process = None
        self.log_path = None
        self.port = None
        self.started_by_us = False

    def _pick_port(self):
        explicit = os.environ.get("TICKETPATH_TEST_PORT")
        if explicit:
            port = int(explicit)
            if port in RESERVED_PORTS:
                raise RuntimeError(f"refusing port {port}: it is reserved on this machine")
            if not _port_free(port):
                raise RuntimeError(f"TICKETPATH_TEST_PORT={port} is already in use")
            return port
        if _port_free(8788):
            return 8788
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        return port

    def start(self):
        if self.base_url:
            status, _ = raw_get(self.base_url + "/health")
            if status != 200:
                raise RuntimeError(f"{self.base_url}/health answered {status}")
            return self
        self.port = self._pick_port()
        if self.port in RESERVED_PORTS:
            raise RuntimeError(f"refusing port {self.port}: it is reserved on this machine")
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.log_path = os.path.join(tempfile.gettempdir(), f"ticketpath-contract-{self.port}.log")
        log = open(self.log_path, "wb")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "ticketpath.server", "--port", str(self.port)],
            cwd=REPO_ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log.close()
        self.started_by_us = True
        deadline = time.time() + 20
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(
                    f"server exited with {self.process.returncode}; see {self.log_path}"
                )
            status, _ = raw_get(self.base_url + "/health")
            if status == 200:
                return self
            time.sleep(0.1)
        raise RuntimeError(f"server did not answer /health in 20s; see {self.log_path}")

    def stop(self):
        if self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self.process = None


def _port_free(port):
    probe = socket.socket()
    # Match what ThreadingHTTPServer does (allow_reuse_address), otherwise a port
    # in TIME_WAIT reads as busy while the server could in fact bind it.
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        probe.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        probe.close()


def raw_get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, {}
    except (urllib.error.URLError, ConnectionError, socket.timeout, OSError):
        return 0, {}


def _loads(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return {"unparsable": raw[:200].decode("utf-8", "replace")}


class Client:
    def __init__(self, base_url):
        self.base_url = base_url

    def request(self, method, path, body=None):
        data = None
        headers = {"accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["content-type"] = "application/json"
        request = urllib.request.Request(
            self.base_url + path, data=data, method=method, headers=headers
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, _loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, _loads(exc.read())
        except (urllib.error.URLError, ConnectionError, socket.timeout, OSError) as exc:
            return 0, {"transportError": str(exc)}

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, body=None):
        return self.request("POST", path, body)


def quote(segment):
    return urllib.parse.quote(str(segment), safe="")


def preflight_errors(client):
    """The browser gate on the two POST routes.

    The verify page is a client component: it POSTs JSON from localhost:3000 to
    the API origin, which is a preflighted request. Without the right CORS
    answer the browser blocks it and the page can never verify a wallet, so this
    is checked on the wire rather than read out of the server code.
    """
    url = client.base_url + "/api/wallets/11111111111111111111111111111111/verification"
    request = urllib.request.Request(
        url,
        method="OPTIONS",
        headers={
            "origin": "http://localhost:3000",
            "access-control-request-method": "POST",
            "access-control-request-headers": "content-type",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
            headers = {key.lower(): value for key, value in response.headers.items()}
    except urllib.error.HTTPError as exc:
        status = exc.code
        headers = {key.lower(): value for key, value in exc.headers.items()}
    except (urllib.error.URLError, ConnectionError, socket.timeout, OSError) as exc:
        return [f"preflight: {exc}"]

    errors = []
    if status not in (200, 204):
        errors.append(f"preflight: OPTIONS answered {status}, a browser expects 200/204")
    origin = headers.get("access-control-allow-origin")
    if origin not in ("*", "http://localhost:3000"):
        errors.append(
            f"preflight: access-control-allow-origin is {origin!r}; a browser on localhost:3000 "
            "blocks the POST without it"
        )
    if "post" not in headers.get("access-control-allow-methods", "").lower():
        errors.append(
            f"preflight: access-control-allow-methods is "
            f"{headers.get('access-control-allow-methods')!r} and does not allow POST"
        )
    if "content-type" not in headers.get("access-control-allow-headers", "").lower():
        errors.append(
            f"preflight: access-control-allow-headers is "
            f"{headers.get('access-control-allow-headers')!r} and does not allow content-type"
        )
    return errors


# ---------------------------------------------------------------------------
# The world: path parameters and cross-route facts, discovered not assumed.
# ---------------------------------------------------------------------------

OBSERVATIONS = []


def build_world(client):
    world = {"notes": [], "errors": []}
    status, health = client.get("/health")
    world["health"] = health if isinstance(health, dict) else {}
    cluster = (world["health"].get("chain") or {}).get("cluster")
    world["cluster"] = cluster if isinstance(cluster, str) else "devnet"
    world["now"] = world["health"].get("now")

    status, page = client.get("/api/events?limit=200")
    world["events"] = page.get("items", []) if isinstance(page, dict) else []
    if status != 200 or not isinstance(page.get("items"), list):
        world["errors"].append(f"GET /api/events?limit=200 returned {status}")

    status, page = client.get("/api/tickets?limit=200")
    world["tickets"] = page.get("items", []) if isinstance(page, dict) else []
    if status != 200 or not isinstance(page.get("items"), list):
        world["errors"].append(f"GET /api/tickets?limit=200 returned {status}")

    world["face_by_tier"] = {}
    world["event_by_id"] = {}
    for event in world["events"]:
        if not isinstance(event, dict):
            continue
        world["event_by_id"][event.get("id")] = event
        for tier in event.get("tiers") or []:
            if isinstance(tier, dict):
                world["face_by_tier"][tier.get("id")] = tier.get("faceValueLamports")

    world["histories"] = {}
    for ticket in world["tickets"]:
        if not isinstance(ticket, dict) or not ticket.get("id"):
            continue
        status, history = client.get(f"/api/tickets/{quote(ticket['id'])}/resale-history")
        if status == 200 and isinstance(history, dict):
            world["histories"][ticket["id"]] = history

    world["analytics"] = {}
    for event in world["events"]:
        if not isinstance(event, dict) or not event.get("id"):
            continue
        status, analytics = client.get(f"/api/events/{quote(event['id'])}/analytics")
        if status == 200 and isinstance(analytics, dict):
            world["analytics"][event["id"]] = analytics

    world["event_id"] = world["events"][0]["id"] if world["events"] else None
    world["event_slug"] = world["events"][0].get("slug") if world["events"] else None
    world["ticket_id"] = world["tickets"][0]["id"] if world["tickets"] else None
    world["ticket_mint"] = world["tickets"][0].get("mintAddress") if world["tickets"] else None

    with_sales = [
        ticket["id"]
        for ticket in world["tickets"]
        if isinstance(ticket, dict)
        and any(
            entry.get("kind") == "sale"
            for entry in (world["histories"].get(ticket.get("id"), {}).get("entries") or [])
        )
    ]
    world["ticket_with_sales"] = with_sales[0] if with_sales else world["ticket_id"]
    world["ticket_without_sales"] = next(
        (
            ticket["id"]
            for ticket in world["tickets"]
            if isinstance(ticket, dict) and ticket.get("id") not in with_sales
        ),
        None,
    )
    events_with_sales = [
        event_id
        for event_id, analytics in world["analytics"].items()
        if (analytics.get("saleCount") or 0) > 0
    ]
    world["event_with_sales"] = events_with_sales[0] if events_with_sales else world["event_id"]

    # Deterministic wallets: one the read route asks about (and never verifies),
    # one the POST route verifies, one used to try a crossed nonce.
    world["seed_unknown"] = hashlib.sha256(b"ticketpath-contract-unknown").digest()
    world["seed_signer"] = hashlib.sha256(b"ticketpath-contract-signer").digest()
    world["seed_other"] = hashlib.sha256(b"ticketpath-contract-other").digest()
    world["wallet_unknown"] = b58encode(ed25519_public_key(world["seed_unknown"]))
    world["wallet_signer"] = b58encode(ed25519_public_key(world["seed_signer"]))
    world["wallet_other"] = b58encode(ed25519_public_key(world["seed_other"]))
    return world


# ---------------------------------------------------------------------------
# Semantics. Each returns a list of disagreements, in the same
# "path: what is wrong" shape as the structural errors, plus observations that
# go into the report but do not fail anything.
# ---------------------------------------------------------------------------

def _items(response):
    return response.get("items") if isinstance(response, dict) else None


def sem_health(client, payload, world):
    errors = []
    if payload.get("service") != "ticketpath":
        errors.append(f"/health.service: expected 'ticketpath', got {payload.get('service')!r}")
    if not isinstance(payload.get("version"), str) or not payload.get("version"):
        errors.append("/health.version: expected a non-empty string")
    source = payload.get("dataSource") or {}
    if not isinstance(source.get("synthetic"), bool):
        errors.append("/health.dataSource.synthetic: expected a boolean")
    if source.get("synthetic") is True and "SYNTHETIC" not in str(source.get("label", "")).upper():
        errors.append("/health.dataSource.label: synthetic data must say so")
    contract = payload.get("contract") or {}
    if contract.get("endpointsInContract") != 9:
        errors.append(
            "/health.contract.endpointsInContract: API_CONTRACT.md defines 9 routes, "
            f"server reports {contract.get('endpointsInContract')!r}"
        )
    if contract.get("endpointsImplemented") != contract.get("endpointsInContract"):
        errors.append(
            f"/health.contract: {contract.get('endpointsImplemented')!r} of "
            f"{contract.get('endpointsInContract')!r} contract endpoints implemented"
        )
    return errors


def sem_events_list(client, payload, world):
    errors = []
    items = payload["items"]
    starts = []
    for index, event in enumerate(items):
        path = f"/api/events.items[{index}]"
        try:
            starts.append(_parse_iso(event["startsAt"]))
        except (KeyError, ValueError):
            continue
        tier_total = sum(tier["totalSupply"] for tier in event["tiers"])
        tier_issued = sum(tier["issuedCount"] for tier in event["tiers"])
        if event["totalSupply"] != tier_total:
            errors.append(
                f"{path}.totalSupply: tiers sum to {tier_total}, response says {event['totalSupply']}"
            )
        if event["issuedCount"] != tier_issued:
            errors.append(
                f"{path}.issuedCount: tiers sum to {tier_issued}, response says {event['issuedCount']}"
            )
        if tier_issued > tier_total:
            errors.append(f"{path}.issuedCount: issued {tier_issued} exceeds supply {tier_total}")
    if starts != sorted(starts):
        errors.append("/api/events: the contract requires startsAt ascending; the page is not sorted")
    ids = [event["id"] for event in items]
    if len(ids) != len(set(ids)):
        errors.append("/api/events: duplicate event ids in one page")

    if items:
        one = items[0]
        status, filtered = client.get(f"/api/events?status={quote(one['status'])}")
        if status != 200:
            errors.append(f"/api/events?status=: expected 200, got {status}")
        else:
            bad = [item["id"] for item in _items(filtered) or [] if item["status"] != one["status"]]
            if bad:
                errors.append(
                    f"/api/events?status={one['status']}: returned rows outside the filter: {bad}"
                )
        status, filtered = client.get(f"/api/events?city={quote(str(one['city']).lower())}")
        if status != 200:
            errors.append(f"/api/events?city=: expected 200, got {status}")
        elif not any(item["id"] == one["id"] for item in _items(filtered) or []):
            errors.append(
                "/api/events?city=: the contract does not say the match is case-sensitive, and a "
                f"lower-cased city did not match {one['city']!r}"
            )
        needle = str(one["venue"]).split()[0]
        status, filtered = client.get(f"/api/events?q={quote(needle)}")
        if status != 200:
            errors.append(f"/api/events?q=: expected 200, got {status}")
        elif not any(item["id"] == one["id"] for item in _items(filtered) or []):
            errors.append(
                f"/api/events?q={needle}: free text must match name and venue; {one['id']} was not returned"
            )

    # Cursor pagination must walk the collection exactly once.
    status, first = client.get("/api/events?limit=1")
    walked = [item["id"] for item in _items(first) or []]
    cursor = first.get("nextCursor") if isinstance(first, dict) else None
    pages = 0
    while cursor is not None and pages < 500:
        pages += 1
        status, page = client.get(f"/api/events?limit=1&cursor={quote(cursor)}")
        if status != 200:
            errors.append(f"/api/events?cursor={cursor}: expected 200, got {status}")
            break
        for item in _items(page) or []:
            if item["id"] in walked:
                errors.append(f"/api/events: the cursor walk repeated {item['id']}")
            walked.append(item["id"])
        cursor = page.get("nextCursor")
    if pages >= 500:
        errors.append("/api/events: the cursor walk did not terminate in 500 pages")
    if set(walked) != set(ids):
        errors.append(
            f"/api/events: the cursor walk visited {len(set(walked))} events; the collection has {len(ids)}"
        )
    return errors


def _contract_view(payload, schema):
    """Only the fields the contract defines, so declared additions do not mask a
    real disagreement between two routes that describe the same object."""
    return {key: payload.get(key) for key in schema}


def sem_event_detail(client, payload, world):
    errors = []
    # Every event in the collection, not just the one this row addresses: the
    # detail route is the one the frontend routes on slug, so all of them must
    # resolve both ways and agree with the list.
    seen = {payload["id"]}
    targets = [payload] + [
        event for event in world["events"] if event.get("id") not in seen
    ]
    for expected in targets:
        event_id, slug = expected["id"], expected["slug"]
        status, by_id = client.get(f"/api/events/{quote(event_id)}")
        if status != 200:
            errors.append(f"/api/events/{event_id}: id lookup returned {status}")
        elif _contract_view(by_id, EVENT[1]) != _contract_view(expected, EVENT[1]):
            errors.append(
                f"/api/events/{event_id}: the detail payload differs from the same event in "
                "/api/events; the list and the detail disagree"
            )
        status, by_slug = client.get(f"/api/events/{quote(slug)}")
        if status != 200:
            errors.append(f"/api/events/{slug}: the contract says the slug resolves; got {status}")
        elif _contract_view(by_slug, EVENT[1]) != _contract_view(expected, EVENT[1]):
            errors.append(
                f"/api/events/{slug}: the slug is the route the frontend uses; its payload differs "
                "from the id lookup"
            )
        tier_total = sum(tier["totalSupply"] for tier in expected["tiers"])
        if expected["totalSupply"] != tier_total:
            errors.append(f"/api/events/{event_id}.totalSupply: tiers sum to {tier_total}")
        for index, tier in enumerate(expected["tiers"]):
            if tier["faceValueLamports"] <= 0:
                errors.append(
                    f"/api/events/{event_id}.tiers[{index}].faceValueLamports: face value is the "
                    "denominator of every markup; 0 is unusable"
                )
            if tier["issuedCount"] > tier["totalSupply"]:
                errors.append(
                    f"/api/events/{event_id}.tiers[{index}]: issuedCount exceeds totalSupply"
                )
        if expected["issuedCount"] != sum(tier["issuedCount"] for tier in expected["tiers"]):
            errors.append(f"/api/events/{event_id}.issuedCount: does not equal the sum of the tiers")
        if expected["resalePriceCapBps"] is not None and expected["resalePriceCapBps"] < 0:
            errors.append(
                f"/api/events/{event_id}.resalePriceCapBps: {expected['resalePriceCapBps']} is "
                "negative; the contract means bps over face"
            )
        if expected["endsAt"] is not None and _parse_iso(expected["endsAt"]) < _parse_iso(
            expected["startsAt"]
        ):
            errors.append(f"/api/events/{event_id}.endsAt: ends before it starts")
    status, body = client.get("/api/events/evt-does-not-exist-0000")
    if status != 404:
        errors.append(
            f"/api/events/{{unknown}}: the contract says 404, not 200-with-null; got {status}"
        )
    elif not (body.get("message") or body.get("error")):
        errors.append("/api/events/{unknown}: the 404 body carries neither `message` nor `error`")
    return errors


def sem_tickets_list(client, payload, world):
    errors = []
    items = payload["items"]
    for index, ticket in enumerate(items):
        path = f"/api/tickets.items[{index}]"
        tier_id = ticket.get("tierId")
        if tier_id in world["face_by_tier"] and ticket["faceValueLamports"] != world["face_by_tier"][tier_id]:
            errors.append(
                f"{path}.faceValueLamports: {ticket['faceValueLamports']} but tier {tier_id!r} "
                f"has face {world['face_by_tier'][tier_id]}"
            )
        event = world["event_by_id"].get(ticket.get("eventId"))
        if event is not None and tier_id not in {tier["id"] for tier in event["tiers"]}:
            errors.append(f"{path}.tierId: {tier_id!r} is not a tier of event {event['id']}")
    ids = [ticket["id"] for ticket in items]
    if len(ids) != len(set(ids)):
        errors.append("/api/tickets: duplicate ticket ids in one page")

    if items:
        secondary = next(
            (ticket for ticket in items if ticket["ownerWallet"] != ticket["issuedToWallet"]), None
        )
        probe = secondary or items[0]
        owner = probe["ownerWallet"]
        status, filtered = client.get(f"/api/tickets?ownerWallet={quote(owner)}&limit=200")
        if status != 200:
            errors.append(f"/api/tickets?ownerWallet=: expected 200, got {status}")
        else:
            returned = _items(filtered) or []
            wrong = [t["id"] for t in returned if t["ownerWallet"] != owner]
            if wrong:
                errors.append(
                    f"/api/tickets?ownerWallet={owner}: the contract says current on-chain owner; "
                    f"these rows have a different ownerWallet: {wrong}"
                )
            if probe["id"] not in [t["id"] for t in returned]:
                errors.append(
                    f"/api/tickets?ownerWallet={owner}: the holder's own ticket {probe['id']} was not returned"
                )
            if probe["ownerWallet"] != probe["issuedToWallet"]:
                status, issuee_page = client.get(
                    f"/api/tickets?ownerWallet={quote(probe['issuedToWallet'])}&limit=200"
                )
                if probe["id"] in [t["id"] for t in _items(issuee_page) or []]:
                    errors.append(
                        f"/api/tickets?ownerWallet={probe['issuedToWallet']}: returned {probe['id']}, "
                        "which that wallet no longer owns; the filter followed the issuee, not the owner"
                    )
    return errors


def sem_ticket_detail(client, payload, world):
    errors = []
    ticket_id = payload["id"]
    status, by_mint = client.get(f"/api/tickets/{quote(payload['mintAddress'])}")
    if status != 200:
        errors.append(f"/api/tickets/{{mint}}: the contract says a mint address resolves; got {status}")
    elif by_mint != payload:
        errors.append(
            f"/api/tickets/{payload['mintAddress']}: the mint lookup returned a different payload "
            "from the id lookup"
        )
    event = world["event_by_id"].get(payload["eventId"])
    if event is None:
        errors.append(f"/api/tickets/{ticket_id}.eventId: {payload['eventId']!r} is not in /api/events")
    else:
        tier = next((t for t in event["tiers"] if t["id"] == payload["tierId"]), None)
        if tier is None:
            errors.append(f"/api/tickets/{ticket_id}.tierId: {payload['tierId']!r} is not a tier of its event")
        elif payload["faceValueLamports"] != tier["faceValueLamports"]:
            errors.append(
                f"/api/tickets/{ticket_id}.faceValueLamports: {payload['faceValueLamports']} "
                f"but its own tier face is {tier['faceValueLamports']}"
            )
    history = world["histories"].get(ticket_id)
    if history is None:
        errors.append(f"/api/tickets/{ticket_id}: no resale-history to check the ticket against")
    else:
        entries = history["entries"]
        sales = [e for e in entries if e["kind"] == "sale" and e["priceLamports"] is not None]
        expected_last = sales[-1]["priceLamports"] if sales else None
        if payload["lastSalePriceLamports"] != expected_last:
            errors.append(
                f"/api/tickets/{ticket_id}.lastSalePriceLamports: {payload['lastSalePriceLamports']} "
                f"but the last priced sale in the trail is {expected_last}"
            )
        expected_transfers = sum(1 for e in entries if e["kind"] in ("sale", "transfer"))
        if payload["transferCount"] != expected_transfers:
            errors.append(
                f"/api/tickets/{ticket_id}.transferCount: {payload['transferCount']} but the trail "
                f"has {expected_transfers} sale+transfer entries (issue and redeem excluded by contract)"
            )
        issue = [e for e in entries if e["kind"] == "issue"]
        if issue and payload["issuedAt"] != issue[0]["occurredAt"]:
            errors.append(
                f"/api/tickets/{ticket_id}.issuedAt: {payload['issuedAt']} but the issue entry is "
                f"{issue[0]['occurredAt']}"
            )
        if payload["status"] == "redeemed" and payload["redeemedAt"] is None:
            errors.append(
                f"/api/tickets/{ticket_id}.redeemedAt: status is 'redeemed' but redeemedAt is null"
            )
        if payload["status"] != "redeemed" and payload["redeemedAt"] is not None:
            errors.append(
                f"/api/tickets/{ticket_id}: redeemedAt is set but status is {payload['status']!r}"
            )
    status, body = client.get("/api/tickets/tkt-does-not-exist-0000")
    if status != 404:
        errors.append(f"/api/tickets/{{unknown}}: expected 404, got {status}")
    elif not (body.get("message") or body.get("error")):
        errors.append("/api/tickets/{unknown}: the 404 body carries neither `message` nor `error`")
    return errors


def sem_resale_history(client, payload, world):
    errors = []
    ticket_id = payload["ticketId"]
    face = payload["faceValueLamports"]
    entries = payload["entries"]
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)):
        errors.append(f"/api/tickets/{ticket_id}/resale-history: duplicate entry ids")
    moments = [_parse_iso(entry["occurredAt"]) for entry in entries]
    if moments != sorted(moments):
        errors.append(
            f"/api/tickets/{ticket_id}/resale-history.entries: the contract says chronological, "
            "oldest first; the list is not sorted"
        )
    for index, entry in enumerate(entries):
        path = f"/api/tickets/{ticket_id}/resale-history.entries[{index}]"
        if entry["ticketId"] != ticket_id:
            errors.append(f"{path}.ticketId: {entry['ticketId']!r} inside the trail of {ticket_id!r}")
        price, markup = entry["priceLamports"], entry["markupBps"]
        if price is None and markup is not None:
            errors.append(
                f"{path}.markupBps: {markup} on an unpriced {entry['kind']!r} move; the contract "
                "says priceLamports and markupBps are null together"
            )
        if price is not None and markup is None:
            errors.append(f"{path}.markupBps: null on a priced {entry['kind']!r} move at {price}")
        if price is not None and markup is not None:
            expected = markup_bps(price, face)
            if markup != expected:
                errors.append(
                    f"{path}.markupBps: {markup} but {price} against this ticket's own face {face} "
                    f"is {expected} bps (the contract forbids re-deriving markup at event level)"
                )
        if entry["kind"] == "sale" and price is None:
            errors.append(f"{path}.priceLamports: a sale is money changing hands; price is null")
    if entries and not any(entry["kind"] == "issue" for entry in entries):
        errors.append(
            f"/api/tickets/{ticket_id}/resale-history.entries: no `issue` row; the custody trail "
            "the contract asks for is incomplete"
        )

    stats = payload["stats"]
    sales = [entry for entry in entries if entry["kind"] == "sale" and entry["priceLamports"] is not None]
    prices = [entry["priceLamports"] for entry in sales]
    markups = [entry["markupBps"] for entry in sales if entry["markupBps"] is not None]
    wallets = set()
    for entry in entries:
        for side in ("fromWallet", "toWallet"):
            if entry[side]:
                wallets.add(entry[side])
    expected = {
        "saleCount": len(sales),
        "transferCount": sum(1 for e in entries if e["kind"] in ("sale", "transfer")),
        "avgMarkupBps": integer_mean(markups),
        "peakPriceLamports": max(prices) if prices else None,
        "lastPriceLamports": prices[-1] if prices else None,
        "totalVolumeLamports": sum(prices),
        "uniqueWallets": len(wallets),
    }
    for field, want in expected.items():
        got = stats[field]
        if got != want:
            errors.append(
                f"/api/tickets/{ticket_id}/resale-history.stats.{field}: the contract's rule over "
                f"these entries gives {want}, response says {got}"
            )
    status, body = client.get("/api/tickets/tkt-does-not-exist-0000/resale-history")
    if status != 404:
        errors.append(f"/api/tickets/{{unknown}}/resale-history: expected 404, got {status}")
    return errors


def sem_wallet_verification_get(client, payload, world):
    errors = []
    wallet = world["wallet_unknown"]
    if payload["wallet"] != wallet:
        errors.append(
            f"/api/wallets/{{wallet}}/verification.wallet: the contract echoes the path; sent "
            f"{wallet!r}, got {payload['wallet']!r}"
        )
    if payload["verified"] is not False:
        errors.append(
            "/api/wallets/{wallet}/verification: the contract says an unknown wallet is 200 with "
            "verified:false, not verified:true"
        )
    if payload["verifiedAt"] is not None:
        errors.append("/api/wallets/{wallet}/verification.verifiedAt: unverified wallet must be null")
    if payload["method"] is not None:
        errors.append("/api/wallets/{wallet}/verification.method: unverified wallet must be null")
    if not payload["flags"]:
        errors.append(
            "/api/wallets/{wallet}/verification.flags: the contract defines flags as the reasons a "
            "capability is false, and both capabilities are false here"
        )
    if payload["canPurchase"] and not payload["verified"]:
        errors.append("/api/wallets/{wallet}/verification.canPurchase: true for an unverified wallet")
    status, body = client.get("/api/wallets/0OIl-not-base58/verification")
    if status != 400:
        errors.append(f"/api/wallets/{{malformed}}/verification: expected 400, got {status}")
    elif not (body.get("message") or body.get("error")):
        errors.append("/api/wallets/{malformed}/verification: the 400 body carries no `message`/`error`")
    return errors


def sem_challenge(client, payload, world):
    errors = []
    nonce, expires_at = payload["nonce"], payload["expiresAt"]
    if len(nonce) < 8:
        errors.append(
            f"/api/wallets/{{wallet}}/verification/challenge.nonce: {nonce!r} is too short to be a nonce"
        )
    if re.search(r"\s", nonce):
        errors.append(
            f"/api/wallets/{{wallet}}/verification/challenge.nonce: {nonce!r} contains whitespace"
        )
    if not world.get("now"):
        errors.append("/health.now is missing, so challenge expiry cannot be judged")
    elif _parse_iso(expires_at) <= _parse_iso(world["now"]):
        errors.append(
            f"/api/wallets/{{wallet}}/verification/challenge.expiresAt: {expires_at} is not in the future"
        )
    return errors


def verification_harness(client, world):
    """Issue a challenge, sign the contract's frozen message, submit it.

    This is the canonical response for the POST route: the route cannot be
    exercised without a real signature, so the harness produces one and the
    structural check runs on the genuine success payload.
    """
    wallet = world["wallet_signer"]
    status, challenge = client.post(f"/api/wallets/{quote(wallet)}/verification/challenge")
    if status != 200 or not isinstance(challenge.get("nonce"), str):
        return status, challenge if isinstance(challenge, dict) else {}
    nonce = challenge["nonce"]
    message = verification_message(wallet, nonce, world["cluster"]).encode("utf-8")
    signature = b58encode(ed25519_sign(world["seed_signer"], message))
    world["signed_nonce"] = nonce
    world["signed_signature"] = signature
    world["signed_wallet"] = wallet
    return client.post(
        f"/api/wallets/{quote(wallet)}/verification",
        {"nonce": nonce, "signature": signature},
    )


def sem_verification_post(client, payload, world):
    errors = []
    wallet = world.get("signed_wallet")
    nonce = world.get("signed_nonce")
    signature = world.get("signed_signature")
    if not (wallet and nonce and signature):
        errors.append(
            "POST /api/wallets/{wallet}/verification: no nonce was issued, so the signed flow "
            "could not be exercised at all"
        )
        return errors

    # Anchor the frozen message shape the signature was made over.
    text = verification_message(wallet, nonce, world["cluster"])
    if text.split("\n")[0] != "Verify wallet ownership for ticket issuance.":
        errors.append("verification_message: the first line is not the contract's first line")
    if text.count("\n") != 4 or text.endswith("\n"):
        errors.append("verification_message: the contract freezes five lines with no trailing newline")

    if payload.get("wallet") != wallet:
        errors.append(
            f"/api/wallets/{{wallet}}/verification.wallet: expected {wallet!r}, got {payload.get('wallet')!r}"
        )
    if payload.get("verified") is not True:
        errors.append(
            "/api/wallets/{wallet}/verification.verified: a valid signature over the frozen "
            f"message must verify the wallet; response says {payload.get('verified')!r}"
        )
    if payload.get("method") != "wallet_signature":
        errors.append(
            f"/api/wallets/{{wallet}}/verification.method: expected 'wallet_signature', got "
            f"{payload.get('method')!r}"
        )
    if payload.get("verifiedAt") is None:
        errors.append("/api/wallets/{wallet}/verification.verifiedAt: must be set on success")
    if payload.get("canPurchase") is not True or payload.get("canReceiveTransfer") is not True:
        errors.append(
            "/api/wallets/{wallet}/verification: a verified wallet must have canPurchase and "
            "canReceiveTransfer true; they are the flags that gate the buy and transfer flows"
        )

    # Single-use nonce: replaying the same signed message must be refused.
    status, replay = client.post(
        f"/api/wallets/{quote(wallet)}/verification",
        {"nonce": nonce, "signature": signature},
    )
    if status != 400:
        errors.append(
            "/api/wallets/{wallet}/verification: the contract says the nonce is single use; the "
            f"replay returned {status}"
        )
    elif not (replay.get("message") or replay.get("error")):
        errors.append("/api/wallets/{wallet}/verification: the replay refusal carries no message")

    # The verified state must be visible on the read route in the same process.
    status, view = client.get(f"/api/wallets/{quote(wallet)}/verification")
    if status != 200 or view.get("verified") is not True:
        errors.append(
            f"/api/wallets/{{wallet}}/verification: GET after a successful POST returned {status} "
            f"with verified={view.get('verified')!r}"
        )

    # A nonce issued to one wallet must not verify another.
    other = world["wallet_other"]
    status, challenge = client.post(f"/api/wallets/{quote(other)}/verification/challenge")
    if status == 200 and isinstance(challenge.get("nonce"), str):
        crossed = verification_message(other, challenge["nonce"], world["cluster"]).encode("utf-8")
        crossed_signature = b58encode(ed25519_sign(world["seed_other"], crossed))
        status, body = client.post(
            f"/api/wallets/{quote(wallet)}/verification",
            {"nonce": challenge["nonce"], "signature": crossed_signature},
        )
        if status != 400:
            errors.append(
                "/api/wallets/{wallet}/verification: a nonce issued to a different wallet was "
                f"accepted with {status}"
            )
    return errors


def sem_analytics(client, payload, world):
    """Every event's roll-up, so a day-bucket or markup bug cannot hide on one."""
    errors = _analytics_errors(client, payload, world)
    for other_id, other in world["analytics"].items():
        if other_id != payload["eventId"]:
            errors.extend(_analytics_errors(client, other, world))
    status, body = client.get("/api/events/evt-does-not-exist-0000/analytics")
    if status != 404:
        errors.append(
            f"/api/events/{{unknown}}/analytics: expected 404, never an empty roll-up; got {status}"
        )
    return errors


def _analytics_errors(client, payload, world):
    errors = []
    event_id = payload["eventId"]
    event = world["event_by_id"].get(event_id)
    if event is None:
        errors.append(f"/api/events/{event_id}/analytics.eventId: {event_id!r} is not in /api/events")
        return errors

    faces = [tier["faceValueLamports"] for tier in event["tiers"]]
    lowest_face = min(faces) if faces else 0
    if payload["faceValueLamports"] != lowest_face:
        errors.append(
            f"/api/events/{event_id}/analytics.faceValueLamports: the contract says the lowest "
            f"tier face, {lowest_face}; response says {payload['faceValueLamports']}"
        )

    status, page = client.get(f"/api/tickets?eventId={quote(event_id)}&limit=200")
    tickets = _items(page) or []
    sales = []  # (entry, ticket)
    for ticket in tickets:
        history = world["histories"].get(ticket["id"])
        if not history:
            continue
        for entry in history["entries"]:
            if entry["kind"] == "sale" and entry["priceLamports"] is not None:
                sales.append((entry, ticket))
    prices = [entry["priceLamports"] for entry, _ in sales]
    # Each sale is measured against ITS OWN ticket's tier face, never the event's.
    markups = [markup_bps(entry["priceLamports"], ticket["faceValueLamports"]) for entry, ticket in sales]

    expected = {
        "totalVolumeLamports": sum(prices),
        "saleCount": len(sales),
        "avgMarkupBps": integer_mean(markups),
        "medianResalePriceLamports": median_int(prices),
        "uniqueHolders": len({ticket["ownerWallet"] for ticket in tickets}),
    }
    for field, want in expected.items():
        got = payload[field]
        if got != want:
            errors.append(
                f"/api/events/{event_id}/analytics.{field}: the contract's rule over the event's "
                f"tickets gives {want}, response says {got}"
            )

    # Quote the number the forbidden event-level derivation would give, so the
    # report shows the test can tell the two apart on this very event.
    if prices:
        naive_total = markup_bps(integer_mean(prices), lowest_face)
        OBSERVATIONS.append(
            f"/api/events/{event_id}/analytics.avgMarkupBps: reported "
            f"{payload['avgMarkupBps']}; the per-ticket mean is {integer_mean(markups)}; deriving "
            f"it from the mean price and the event-level face would read {naive_total}"
        )
    else:
        OBSERVATIONS.append(
            f"/api/events/{event_id}/analytics: no priced sales, so the markup figures are null/zero"
        )

    issued = event["issuedCount"]
    if issued != len(tickets):
        errors.append(
            f"/api/events/{event_id}.issuedCount: {issued} but /api/tickets returns {len(tickets)} "
            "tickets for the event; resoldShare has no unambiguous denominator"
        )
    resold = {entry["ticketId"] for entry, _ in sales}
    want_share = (len(resold) / issued) if issued else 0.0
    if abs(float(payload["resoldShare"]) - want_share) > 1e-9:
        errors.append(
            f"/api/events/{event_id}/analytics.resoldShare: {len(resold)} resold of {issued} issued "
            f"is {want_share}, response says {payload['resoldShare']}"
        )

    # Day buckets, UTC, ascending; average price and average per-sale markup.
    by_day = {}
    for (entry, _ticket), markup in zip(sales, markups):
        slot = by_day.setdefault(utc_day(entry["occurredAt"]), {"prices": [], "markups": []})
        slot["prices"].append(entry["priceLamports"])
        slot["markups"].append(markup)
    series = payload["priceSeries"]
    dates = [point["date"] for point in series]
    if dates != sorted(dates):
        errors.append(f"/api/events/{event_id}/analytics.priceSeries: dates are not ascending")
    if dates != sorted(by_day):
        errors.append(
            f"/api/events/{event_id}/analytics.priceSeries: days {dates}; the event's sales fall on "
            f"{sorted(by_day)}"
        )
    for point in series:
        day = point["date"]
        slot = by_day.get(day)
        if slot is None:
            continue
        want_price = integer_mean(slot["prices"])
        if point["avgPriceLamports"] != want_price:
            errors.append(
                f"/api/events/{event_id}/analytics.priceSeries[{day}].avgPriceLamports: mean of "
                f"{slot['prices']} is {want_price}, response says {point['avgPriceLamports']}"
            )
        if point["saleCount"] != len(slot["prices"]):
            errors.append(
                f"/api/events/{event_id}/analytics.priceSeries[{day}].saleCount: "
                f"{len(slot['prices'])} sales that day, response says {point['saleCount']}"
            )
        want_markup = integer_mean(slot["markups"])
        if point["avgMarkupBps"] != want_markup:
            errors.append(
                f"/api/events/{event_id}/analytics.priceSeries[{day}].avgMarkupBps: the mean of "
                f"that day's per-sale markups is {want_markup}, response says {point['avgMarkupBps']}"
            )
        naive = markup_bps(point["avgPriceLamports"], lowest_face)
        if naive != want_markup and point["avgMarkupBps"] != want_markup:
            OBSERVATIONS.append(
                f"/api/events/{event_id}/analytics.priceSeries[{day}]: the forbidden event-level "
                f"derivation would read {naive} bps; the per-ticket mean is {want_markup}"
            )

    # Distribution: all six buckets, the contract's order and bounds, counts
    # over the event's priced sales.
    buckets = payload["markupDistribution"]
    if len(buckets) != len(CONTRACT_MARKUP_BUCKETS):
        errors.append(
            f"/api/events/{event_id}/analytics.markupDistribution: expected "
            f"{len(CONTRACT_MARKUP_BUCKETS)} buckets, got {len(buckets)}"
        )
    counts = {row[0]: 0 for row in CONTRACT_MARKUP_BUCKETS}
    for markup in markups:
        counts[bucket_label(markup)] += 1
    for index, (label, from_bps, to_bps) in enumerate(CONTRACT_MARKUP_BUCKETS):
        if index >= len(buckets):
            break
        bucket = buckets[index]
        if bucket["label"] != label:
            errors.append(
                f"/api/events/{event_id}/analytics.markupDistribution[{index}].label: the "
                f"contract's table says {label!r}, response says {bucket['label']!r}"
            )
        if bucket["fromBps"] != from_bps:
            errors.append(
                f"/api/events/{event_id}/analytics.markupDistribution[{index}].fromBps: contract "
                f"says {from_bps}, response says {bucket['fromBps']}"
            )
        if bucket["toBps"] != to_bps:
            errors.append(
                f"/api/events/{event_id}/analytics.markupDistribution[{index}].toBps: contract "
                f"says {to_bps}, response says {bucket['toBps']}"
            )
        if bucket["count"] != counts[label]:
            errors.append(
                f"/api/events/{event_id}/analytics.markupDistribution[{index}].count: "
                f"{counts[label]} of the event's sales fall in this bucket, response says {bucket['count']}"
            )
    total_counted = sum(bucket["count"] for bucket in buckets)
    if total_counted != len(sales):
        errors.append(
            f"/api/events/{event_id}/analytics.markupDistribution: the buckets sum to "
            f"{total_counted}, but there are {len(sales)} priced sales"
        )

    # Where tickets ended up.
    holdings = {}
    for ticket in tickets:
        slot = holdings.setdefault(ticket["ownerWallet"], {"count": 0, "secondary": False})
        slot["count"] += 1
        if ticket["ownerWallet"] != ticket["issuedToWallet"]:
            slot["secondary"] = True
    rows = payload["topDestinations"]
    if len(rows) > 12:
        errors.append(
            f"/api/events/{event_id}/analytics.topDestinations: {len(rows)} rows; the contract caps near 12"
        )
    counts_desc = [row["ticketCount"] for row in rows]
    if counts_desc != sorted(counts_desc, reverse=True):
        errors.append(
            f"/api/events/{event_id}/analytics.topDestinations: not sorted by ticketCount descending"
        )
    wallets = [row["wallet"] for row in rows]
    if len(wallets) != len(set(wallets)):
        errors.append(f"/api/events/{event_id}/analytics.topDestinations: a wallet appears twice")
    for row in rows:
        want = holdings.get(row["wallet"])
        if want is None:
            errors.append(
                f"/api/events/{event_id}/analytics.topDestinations: {row['wallet']} does not hold a "
                "ticket for this event"
            )
            continue
        if row["ticketCount"] != want["count"]:
            errors.append(
                f"/api/events/{event_id}/analytics.topDestinations[{row['wallet']}].ticketCount: "
                f"holds {want['count']}, response says {row['ticketCount']}"
            )
        if row["acquiredOnSecondary"] != want["secondary"]:
            errors.append(
                f"/api/events/{event_id}/analytics.topDestinations[{row['wallet']}].acquiredOnSecondary: "
                f"holder is not the original issuee -> {want['secondary']}, response says "
                f"{row['acquiredOnSecondary']}"
            )
    if len(rows) != min(len(holdings), 12):
        errors.append(
            f"/api/events/{event_id}/analytics.topDestinations: {len(rows)} rows for "
            f"{len(holdings)} distinct holders"
        )
    return errors


# ---------------------------------------------------------------------------
# The route table: one row per route the server serves.
# ---------------------------------------------------------------------------

class Route:
    def __init__(self, name, method, path, schema, semantics, extras=None, gaps=(),
                 harness=None, contract_route=True):
        self.name = name
        self.method = method
        self.path = path            # callable(world) -> request path
        self.schema = schema        # ("object", {...}) for the payload root
        self.semantics = semantics
        self.extras = extras or {}  # declared additions, validated as their own schemas
        self.gaps = gaps            # contract fields no data on this machine can fill
        self.harness = harness      # callable(client, world) -> (status, payload)
        self.contract_route = contract_route


def _const(path):
    return lambda world: path


ROUTES = (
    Route(
        name="GET /health",
        method="GET",
        path=_const("/health"),
        schema=obj({}),  # not a contract type: everything it carries is declared here
        semantics=sem_health,
        extras={
            "service": STR,
            "version": STR,
            "status": STR,
            "now": ISO,
            "dataSource": DATA_SOURCE,
            "chain": open_obj(),
            "pricingModel": open_obj(),
            "contract": open_obj(),
        },
        contract_route=False,
    ),
    Route(
        name="GET /api/events",
        method="GET",
        path=_const("/api/events"),
        schema=PAGE_EVENT,
        semantics=sem_events_list,
        extras={"dataSource": DATA_SOURCE},
    ),
    Route(
        name="GET /api/events/{idOrSlug}",
        method="GET",
        path=lambda world: f"/api/events/{quote(world['event_id'])}",
        schema=EVENT,
        semantics=sem_event_detail,
        extras={"dataSource": DATA_SOURCE},
        gaps=("imageUrl is always null: no media exists in the repository",),
    ),
    Route(
        name="GET /api/events/{eventId}/analytics",
        method="GET",
        path=lambda world: f"/api/events/{quote(world['event_with_sales'])}/analytics",
        schema=EVENT_ANALYTICS,
        semantics=sem_analytics,
        extras={"dataSource": DATA_SOURCE, "analyticsNote": STR},
        gaps=("topDestinations[].region is always null: no wallet has volunteered a region",),
    ),
    Route(
        name="GET /api/tickets",
        method="GET",
        path=_const("/api/tickets"),
        schema=PAGE_TICKET,
        semantics=sem_tickets_list,
        extras={"dataSource": DATA_SOURCE},
    ),
    Route(
        name="GET /api/tickets/{ticketId}",
        method="GET",
        path=lambda world: f"/api/tickets/{quote(world['ticket_id'])}",
        schema=TICKET,
        semantics=sem_ticket_detail,
        extras={"dataSource": DATA_SOURCE},
        gaps=(
            "mintAddress must be a real SPL mint on the cluster; this is a shape-valid placeholder",
            "transferRestricted must reflect on-chain enforcement; nothing is deployed, so it is false",
        ),
    ),
    Route(
        name="GET /api/tickets/{ticketId}/resale-history",
        method="GET",
        path=lambda world: f"/api/tickets/{quote(world['ticket_with_sales'])}/resale-history",
        schema=RESALE_HISTORY,
        semantics=sem_resale_history,
        extras={"dataSource": DATA_SOURCE, "custodyNote": STR},
        gaps=(
            "signature is always null: no transaction exists, so no Explorer deep-link resolves",
            "slot is always null: same reason",
        ),
    ),
    Route(
        name="GET /api/wallets/{wallet}/verification",
        method="GET",
        path=lambda world: f"/api/wallets/{quote(world['wallet_unknown'])}/verification",
        schema=WALLET_VERIFICATION,
        semantics=sem_wallet_verification_get,
        extras={"dataSource": DATA_SOURCE},
        gaps=("method can only be 'wallet_signature' or null: no identity provider is connected",),
    ),
    Route(
        name="POST /api/wallets/{wallet}/verification/challenge",
        method="POST",
        path=lambda world: f"/api/wallets/{quote(world['wallet_unknown'])}/verification/challenge",
        schema=CHALLENGE,
        semantics=sem_challenge,
        extras={"dataSource": DATA_SOURCE},
    ),
    Route(
        name="POST /api/wallets/{wallet}/verification",
        method="POST",
        path=lambda world: f"/api/wallets/{quote(world['wallet_signer'])}/verification",
        schema=WALLET_VERIFICATION,
        semantics=sem_verification_post,
        extras={"dataSource": DATA_SOURCE},
        harness=verification_harness,
    ),
)

CONTRACT_ROUTE_COUNT = 9  # API_CONTRACT.md lists nine; /health is the tenth, ours.


# ---------------------------------------------------------------------------
# Running it.
# ---------------------------------------------------------------------------

class Result:
    def __init__(self, route, status, payload):
        self.route = route
        self.status = status
        self.payload = payload if isinstance(payload, dict) else {}
        self.structure_errors = []
        self.semantic_errors = []
        self.notes = []
        self.undeclared_extras = []
        self.declared_extras = []
        self.verdict = "UNRUN"

    @property
    def name(self):
        return self.route.name

    @property
    def missing(self):
        return self.verdict == "MISSING"

    def compute_verdict(self):
        if self.status in (0, 404) and not self.structure_errors and not self.semantic_errors:
            if self.status == 0:
                self.verdict = "MISSING"
                self.notes.append(f"no response: {self.payload.get('transportError', 'transport error')}")
            elif self.payload.get("code") == "no_route" or not self.payload:
                self.verdict = "MISSING"
                self.notes.append(f"404: {self.payload.get('message', 'no route')}")
            else:
                self.verdict = "DRIFT"
            return
        if self.structure_errors or self.semantic_errors or self.undeclared_extras:
            self.verdict = "DRIFT"
            return
        self.verdict = "CONFORMANT" if self.route.contract_route else "EXTRA-ROUTE"


def evaluate(route, client, world):
    path = route.path(world)
    if route.harness:
        status, payload = route.harness(client, world)
    else:
        status, payload = client.request(route.method, path, None)
    result = Result(route, status, payload)

    if status == 0:
        result.compute_verdict()
        return result
    if status == 404 and result.payload.get("code") == "no_route":
        result.notes.append("the server serves no such route")
        result.compute_verdict()
        return result
    if not isinstance(payload, dict):
        result.structure_errors.append(f"{route.name}: the response body is not a JSON object")
        result.compute_verdict()
        return result

    schema = route.schema[1]
    check_object(payload, schema, route.name, route.extras, result.structure_errors)
    result.declared_extras = sorted(set(payload) & set(route.extras))
    result.undeclared_extras = sorted(set(payload) - set(schema) - set(route.extras))
    for key in result.undeclared_extras:
        result.structure_errors.append(
            f"{route.name}.{key}: field is neither in the contract nor a declared addition"
        )

    if status >= 400:
        result.structure_errors.append(f"{route.name}: a contract route answered {status}")
        if not (payload.get("message") or payload.get("error")):
            result.structure_errors.append(f"{route.name}: the error body has no `message` or `error`")
        result.compute_verdict()
        return result

    try:
        result.semantic_errors.extend(route.semantics(client, payload, world))
    except Exception as exc:  # noqa: BLE001 - a crashing check is a finding, not a skip
        result.semantic_errors.append(
            f"{route.name}: the semantic check raised {type(exc).__name__}: {exc}"
        )
    result.notes.extend(route.gaps)
    result.compute_verdict()
    return result


_RUN = None


def run_all(server):
    del OBSERVATIONS[:]
    client = Client(server.base_url)
    world = build_world(client)
    results = [evaluate(route, client, world) for route in ROUTES]
    world["preflight_errors"] = preflight_errors(client)
    return client, world, results


# ---------------------------------------------------------------------------
# unittest surface. The whole run happens once, in setUpModule.
# ---------------------------------------------------------------------------

def setUpModule():
    global _RUN
    server = ServerHandle().start()
    try:
        _RUN = (server, *run_all(server))
    except BaseException:
        server.stop()
        raise


def tearDownModule():
    if _RUN is not None:
        _RUN[0].stop()


def _results():
    return _RUN[3] if _RUN else []


class TestHarnessSelfCheck(unittest.TestCase):
    """If these fail, the harness is wrong, not the server."""

    def test_signer_reproduces_rfc8032_vector_1(self):
        seed = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
        self.assertEqual(
            ed25519_public_key(seed).hex(),
            "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
        )
        self.assertEqual(
            ed25519_sign(seed, b"").hex(),
            "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
            "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b",
        )

    def test_base58_roundtrip(self):
        address = "FXTUREorg1111111111111111111111111111111111"
        self.assertEqual(b58encode(b58decode(address)), address)
        self.assertEqual(len(b58decode(address)), 32)

    def test_frozen_message_shape(self):
        text = verification_message("W", "N", "devnet")
        self.assertEqual(len(text.split("\n")), 5)
        self.assertFalse(text.endswith("\n"))
        self.assertEqual(text.split("\n")[2], "Wallet: W")


class TestEveryContractRouteIsServed(unittest.TestCase):
    def test_nine_contract_routes_are_attempted_and_served(self):
        results = _results()
        self.assertEqual(len(results), 10, "nine contract routes plus /health")
        contract = [r for r in results if r.route.contract_route]
        self.assertEqual(len(contract), CONTRACT_ROUTE_COUNT)
        missing = [f"{r.name}: HTTP {r.status} {r.notes}" for r in contract if r.missing]
        self.assertEqual(missing, [], "a route the contract defines is not served")

    def test_every_route_was_evaluated(self):
        for result in _results():
            self.assertNotEqual(result.verdict, "UNRUN", f"{result.name} was never evaluated")


class TestStructure(unittest.TestCase):
    def test_every_route_matches_the_contract_shape(self):
        for result in _results():
            with self.subTest(route=result.name):
                self.assertEqual(
                    result.structure_errors,
                    [],
                    f"{result.name} (HTTP {result.status}):\n  "
                    + "\n  ".join(result.structure_errors),
                )


class TestSemantics(unittest.TestCase):
    def test_every_route_honours_the_contract_prose(self):
        for result in _results():
            with self.subTest(route=result.name):
                self.assertEqual(
                    result.semantic_errors,
                    [],
                    f"{result.name} (HTTP {result.status}):\n  "
                    + "\n  ".join(result.semantic_errors),
                )


class TestDeclaredAdditions(unittest.TestCase):
    def test_only_the_documented_extras_appear(self):
        expected = {
            "GET /health": ["chain", "contract", "dataSource", "now", "pricingModel",
                            "service", "status", "version"],
            "GET /api/events": ["dataSource"],
            "GET /api/events/{idOrSlug}": ["dataSource"],
            "GET /api/events/{eventId}/analytics": ["analyticsNote", "dataSource"],
            "GET /api/tickets": ["dataSource"],
            "GET /api/tickets/{ticketId}": ["dataSource"],
            "GET /api/tickets/{ticketId}/resale-history": ["custodyNote", "dataSource"],
            "GET /api/wallets/{wallet}/verification": ["dataSource"],
            "POST /api/wallets/{wallet}/verification/challenge": ["dataSource"],
            "POST /api/wallets/{wallet}/verification": ["dataSource"],
        }
        for result in _results():
            if result.status == 0:
                continue
            with self.subTest(route=result.name):
                self.assertEqual(
                    result.declared_extras,
                    expected.get(result.name, []),
                    f"{result.name}: additions present are {result.declared_extras}",
                )


class TestNullVersusAbsent(unittest.TestCase):
    """A nullable field must be present and null, never dropped from the object.

    `assertIn` rather than a truthiness test: the contract distinguishes "this
    is null" from "this key is missing", and TypeScript's `T | null` is the
    former.
    """

    def test_envelopes_carry_next_cursor(self):
        for name in ("GET /api/events", "GET /api/tickets"):
            result = next(r for r in _results() if r.name == name)
            with self.subTest(route=name):
                self.assertIn("nextCursor", result.payload)

    def test_event_nullables_are_present(self):
        result = next(r for r in _results() if r.name == "GET /api/events")
        for event in result.payload.get("items", []):
            for field in ("endsAt", "imageUrl", "resalePriceCapBps"):
                with self.subTest(event=event.get("id"), field=field):
                    self.assertIn(field, event, f"{event.get('id')}: {field} must be null, not omitted")

    def test_ticket_nullables_are_present(self):
        result = next(r for r in _results() if r.name == "GET /api/tickets")
        for ticket in result.payload.get("items", []):
            for field in ("lastSalePriceLamports", "redeemedAt"):
                with self.subTest(ticket=ticket.get("id"), field=field):
                    self.assertIn(field, ticket, f"{ticket.get('id')}: {field} must be null, not omitted")


class TestBrowserPreflight(unittest.TestCase):
    """The verify page POSTs JSON from the browser; the preflight must pass."""

    def test_preflight_allows_the_verify_page(self):
        world = _RUN[2]
        self.assertEqual(world.get("preflight_errors"), [], world.get("preflight_errors"))


class TestMissingRouteIsAFinding(unittest.TestCase):
    """A route the contract defines that the server does not answer must report
    MISSING with a reason, not pass silently and not be skipped."""

    def test_absent_route_is_missing_not_skipped(self):
        route = Route(
            name="GET /api/does-not-exist",
            method="GET",
            path=lambda world: "/api/does-not-exist",
            schema=PAGE_EVENT,
            semantics=lambda client, payload, world: [],
        )
        for status, payload in (
            (404, {"message": "no route for /api/does-not-exist", "status": 404, "code": "no_route"}),
            (0, {"transportError": "connection refused"}),
        ):
            result = Result(route, status, payload)
            result.compute_verdict()
            self.assertEqual(result.verdict, "MISSING", f"status {status} must read as MISSING")
            self.assertTrue(result.notes, "a MISSING row must carry the reason")

    def test_a_route_that_answers_400_is_drift_not_missing(self):
        route = Route(
            name="GET /api/broken",
            method="GET",
            path=lambda world: "/api/broken",
            schema=PAGE_EVENT,
            semantics=lambda client, payload, world: [],
        )
        result = Result(route, 400, {"message": "bad request"})
        result.structure_errors.append("answered 400")
        result.compute_verdict()
        self.assertEqual(result.verdict, "DRIFT")


class CannedClient:
    """Serves pre-built responses, so a check can be run against a payload that
    has been deliberately broken. This is how the test proves it can fail."""

    def __init__(self, table):
        self.table = table

    def get(self, path):
        return self.table.get(path, (404, {"message": "no route", "status": 404, "code": "no_route"}))

    def post(self, path, body=None):
        return self.get(path)


def _canned_table(world):
    table = {}
    tickets_by_event = {}
    for ticket in world["tickets"]:
        tickets_by_event.setdefault(ticket["eventId"], []).append(ticket)
    for event in world["events"]:
        table[f"/api/events/{quote(event['id'])}"] = (200, json.loads(json.dumps(event)))
        table[f"/api/events/{quote(event['slug'])}"] = (200, json.loads(json.dumps(event)))
        table[f"/api/tickets?eventId={quote(event['id'])}&limit=200"] = (
            200,
            {
                "items": json.loads(json.dumps(tickets_by_event.get(event["id"], []))),
                "nextCursor": None,
            },
        )
    for ticket_id, history in world["histories"].items():
        table[f"/api/tickets/{quote(ticket_id)}/resale-history"] = (
            200,
            json.loads(json.dumps(history)),
        )
    return table


class TestTheChecksCanFail(unittest.TestCase):
    """Mutation tests: each mutation must be caught, or the check is decoration.

    The payloads are the live responses from this run, so a mutation is exactly
    the drift a backend change would produce.
    """

    def setUp(self):
        self.world = _RUN[2]
        self.client = CannedClient(_canned_table(self.world))
        self.result = next(r for r in _results() if r.name == "GET /api/events/{eventId}/analytics")
        self.analytics = json.loads(json.dumps(self.result.payload))
        self.event = self.world["event_by_id"][self.analytics["eventId"]]
        self.lowest_face = min(tier["faceValueLamports"] for tier in self.event["tiers"])

    def _events_with_sales(self):
        """(event, payload, lowest face, sale prices) for every event with sales."""
        for event_id, payload in self.world["analytics"].items():
            event = self.world["event_by_id"].get(event_id)
            if event is None:
                continue
            prices = []
            for ticket in self.world["tickets"]:
                if ticket["eventId"] != event_id:
                    continue
                for entry in (self.world["histories"].get(ticket["id"]) or {}).get("entries", []):
                    if entry["kind"] == "sale" and entry["priceLamports"] is not None:
                        prices.append(entry["priceLamports"])
            if prices:
                lowest = min(tier["faceValueLamports"] for tier in event["tiers"])
                yield event, json.loads(json.dumps(payload)), lowest, prices

    def test_event_level_markup_is_caught(self):
        """The exact mistake API_CONTRACT.md warns about: one event-level face.

        Only meaningful on a day or event where the two derivations differ, so a
        discriminating candidate is chosen rather than the first one.
        """
        for _event, payload, lowest, prices in self._events_with_sales():
            naive = markup_bps(integer_mean(prices), lowest)
            if naive == payload["avgMarkupBps"]:
                continue
            payload["avgMarkupBps"] = naive
            errors = _analytics_errors(self.client, payload, self.world)
            self.assertTrue(
                any("avgMarkupBps" in error for error in errors),
                f"an event-level markup passed unnoticed: {errors}",
            )
            return
        self.skipTest("no event where the event-level derivation differs from the per-ticket one")

    def test_series_markup_re_derived_from_mean_price_is_caught(self):
        for _event, payload, lowest, _prices in self._events_with_sales():
            for point in payload["priceSeries"]:
                if point["avgMarkupBps"] is None:
                    continue
                naive = markup_bps(point["avgPriceLamports"], lowest)
                if naive == point["avgMarkupBps"]:
                    continue
                point["avgMarkupBps"] = naive
                errors = _analytics_errors(self.client, payload, self.world)
                self.assertTrue(
                    any("avgMarkupBps" in error for error in errors),
                    f"a re-derived series markup passed unnoticed: {errors}",
                )
                return
        self.skipTest("no day where the event-level derivation differs from the per-ticket one")

    def test_wrong_bucket_label_is_caught(self):
        self.analytics["markupDistribution"][1]["label"] = "0-25%"
        errors = _analytics_errors(self.client, self.analytics, self.world)
        self.assertTrue(any("label" in error for error in errors), errors)

    def test_float_money_is_caught(self):
        if not self.analytics["priceSeries"]:
            self.skipTest("no price series on this event")
        self.analytics["priceSeries"][0]["avgPriceLamports"] = float(
            self.analytics["priceSeries"][0]["avgPriceLamports"]
        )
        errors = []
        check_object(self.analytics, EVENT_ANALYTICS[1], "analytics", {"dataSource": DATA_SOURCE}, errors)
        self.assertTrue(
            any("integer count of lamports" in error for error in errors),
            f"a float lamport amount passed unnoticed: {errors}",
        )

    def test_event_level_markup_in_a_ledger_row_is_caught(self):
        ticket_id = next(
            (
                ticket["id"]
                for ticket in self.world["tickets"]
                if any(
                    entry["kind"] == "sale"
                    for entry in self.world["histories"][ticket["id"]]["entries"]
                )
            ),
            None,
        )
        if ticket_id is None:
            self.skipTest("no ticket with a sale")
        history = json.loads(json.dumps(self.world["histories"][ticket_id]))
        sale = next(entry for entry in history["entries"] if entry["kind"] == "sale")
        sale["markupBps"] = markup_bps(sale["priceLamports"], self.lowest_face)
        if sale["markupBps"] == markup_bps(sale["priceLamports"], history["faceValueLamports"]):
            sale["markupBps"] = markup_bps(sale["priceLamports"], self.lowest_face) + 1
        errors = sem_resale_history(self.client, history, self.world)
        self.assertTrue(
            any("markupBps" in error for error in errors),
            f"an event-level ledger markup passed unnoticed: {errors}",
        )

    def test_missing_and_undocumented_fields_are_caught(self):
        payload = json.loads(json.dumps(self.event))
        del payload["endsAt"]
        payload["surpriseField"] = 1
        errors = []
        check_object(payload, EVENT[1], "/api/events/x", {"dataSource": DATA_SOURCE}, errors)
        joined = "\n".join(errors)
        self.assertIn("endsAt", joined, joined)
        self.assertIn("surpriseField", joined, joined)

    def test_bad_enum_and_non_utc_timestamp_are_caught(self):
        payload = json.loads(json.dumps(self.event))
        payload["status"] = "on-sale"
        payload["startsAt"] = "2026-12-01 00:30:00"
        payload["organizer"]["walletAddress"] = "not-a-pubkey"
        errors = []
        check_object(payload, EVENT[1], "/api/events/x", {"dataSource": DATA_SOURCE}, errors)
        joined = "\n".join(errors)
        self.assertIn("outside the contract union", joined, joined)
        self.assertIn("ISO-8601 UTC", joined, joined)
        self.assertIn("walletAddress", joined, joined)


class TestNoDrift(unittest.TestCase):
    def test_no_route_drifts_from_the_contract(self):
        drifted = [r.name for r in _results() if r.verdict == "DRIFT"]
        self.assertEqual(drifted, [], "routes with a contract disagreement: " + ", ".join(drifted))


# ---------------------------------------------------------------------------
# The report.
# ---------------------------------------------------------------------------

def main():
    server = ServerHandle()
    try:
        server.start()
        client, world, results = run_all(server)

        print(f"base url: {server.base_url}")
        if server.log_path:
            print(f"server log: {server.log_path}")
        print(
            f"cluster: {world['cluster']}  "
            f"store: {(world['health'].get('dataSource') or {}).get('mode')}"
        )
        print(f"events: {len(world['events'])}  tickets: {len(world['tickets'])}")
        print()
        print("| route | structure | semantics | verdict |")
        print("|---|---|---|---|")
        for result in results:
            if result.missing:
                structure = semantics = "n/a"
            else:
                structure = "PASS" if not result.structure_errors else f"FAIL ({len(result.structure_errors)})"
                semantics = "PASS" if not result.semantic_errors else f"FAIL ({len(result.semantic_errors)})"
            print(f"| `{result.name}` | {structure} | {semantics} | **{result.verdict}** |")
        print()

        disagreements = 0
        for result in results:
            problems = result.structure_errors + result.semantic_errors
            if not problems:
                continue
            disagreements += len(problems)
            print(f"### {result.name} - {result.verdict} (HTTP {result.status})")
            for problem in problems:
                print(f"- {problem}")
            print()

        print()
        print("browser gate (the verify page POSTs JSON from localhost:3000):")
        browser = world.get("preflight_errors") or []
        if browser:
            for problem in browser:
                print(f"- {problem}")
        else:
            print("- OPTIONS preflight allows the POST: origin, methods and headers all pass")
        print()
        print("declared additions beyond lib/types.ts (CONTRACT-MAP §7.2/§7.3):")
        for result in results:
            if result.declared_extras:
                print(f"- {result.name}: {', '.join(result.declared_extras)}")
        print()
        print("fields the contract defines that no data on this machine can fill:")
        for result in results:
            for gap in result.route.gaps:
                print(f"- {result.name}: {gap}")
        print()
        print("observations (evidence, not failures):")
        for line in OBSERVATIONS:
            print(f"- {line}")
        print()
        print(f"disagreements: {disagreements}")
        return 0 if disagreements == 0 else 1
    finally:
        if server.started_by_us:
            server.stop()
            print(
                f"stopped the server this run started (pid gone, port {server.port}); "
                "no other process was touched"
            )


if __name__ == "__main__":
    if "--table" in sys.argv:
        sys.exit(main())
    unittest.main(module=__name__, argv=[sys.argv[0]], exit=True, verbosity=1)
