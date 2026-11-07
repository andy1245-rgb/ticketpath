#!/usr/bin/env python3
"""Screenshot a running page to PNG, for visual review.

Thin stdlib wrapper around the headless-browser tool at ``~/tools/shot/shot.mjs``.
It shells out to ``node``; the browser lives outside this repository and is a dev
tool only, so nothing here is imported by the backend and no Python dependency is
added. The backend stays stdlib.

    python3 tools/shot.py <url> <out.png> [--width N] [--height N] [--full]
                                         [--mobile] [--json]

Exit codes
    0   PNG written; its absolute path is printed on stdout
    1   capture failed (page unreachable, browser error, unwritable output)
    3   cannot run at all: node missing, tool dir missing, bad arguments

Every capture is capped at 30s by the underlying tool. This wrapper adds a
further 45s subprocess timeout so a wedged node process can never block CI or a
review loop forever.

Examples
    python3 tools/shot.py http://127.0.0.1:8788/ ~/shots/console.png --width 1280
    python3 tools/shot.py http://127.0.0.1:8788/ ~/shots/console-390.png --mobile --full
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 45s = the tool's own 30s watchdog plus room for node startup and PNG encode.
SUBPROCESS_TIMEOUT_S = 45

EXIT_OK = 0
EXIT_CAPTURE_FAILED = 1
EXIT_CANNOT_RUN = 3

DEFAULT_TOOL_DIR = Path.home() / "tools" / "shot"


def tool_dir() -> Path:
    """Where shot.mjs lives. Override with $SHOT_TOOL_DIR."""
    env = os.environ.get("SHOT_TOOL_DIR")
    return Path(env).expanduser() if env else DEFAULT_TOOL_DIR


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="shot.py",
        description="Screenshot a URL to PNG with a headless browser (dev tool).",
        add_help=True,
    )
    p.add_argument("url", help="page to capture, e.g. http://127.0.0.1:8788/")
    p.add_argument("out", help="output .png path (parent dirs are created)")
    p.add_argument("--width", type=int, default=1280, help="viewport width (default 1280)")
    p.add_argument("--height", type=int, default=800, help="viewport height (default 800)")
    p.add_argument("--full", action="store_true", help="capture the full scrollable page")
    p.add_argument("--mobile", action="store_true", help="390x844 viewport, mobile UA")
    p.add_argument("--json", action="store_true", help="print the tool's JSON report instead of the path")
    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)

    if not args.url.startswith(("http://", "https://")):
        print(f"shot.py: url must start with http:// or https://", file=sys.stderr)
        return EXIT_CANNOT_RUN
    if not args.out.lower().endswith(".png"):
        print("shot.py: output must end in .png", file=sys.stderr)
        return EXIT_CANNOT_RUN

    node = shutil.which("node")
    if not node:
        print("shot.py: node not found on PATH", file=sys.stderr)
        return EXIT_CANNOT_RUN

    script = tool_dir() / "shot.mjs"
    if not script.is_file():
        print(
            f"shot.py: {script} is missing — run `npm i playwright && "
            f"npx playwright install chromium` in {tool_dir()}",
            file=sys.stderr,
        )
        return EXIT_CANNOT_RUN

    cmd = [
        node, str(script), args.url, args.out,
        "--width", str(args.width),
        "--height", str(args.height),
    ]
    if args.full:
        cmd.append("--full")
    if args.mobile:
        # --mobile sets its own viewport; pass it last so it wins.
        cmd.append("--mobile")
    if args.json:
        cmd.append("--json")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_S,
            cwd=str(tool_dir()),
        )
    except subprocess.TimeoutExpired:
        print(f"shot.py: timed out after {SUBPROCESS_TIMEOUT_S}s", file=sys.stderr)
        return EXIT_CAPTURE_FAILED
    except OSError as exc:
        print(f"shot.py: could not run node: {exc}", file=sys.stderr)
        return EXIT_CANNOT_RUN

    # The tool uses exit 2 for its own usage errors; treat that as our 3.
    if proc.returncode == 2:
        sys.stderr.write(proc.stderr)
        return EXIT_CANNOT_RUN
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or f"shot.py: node exited {proc.returncode}\n")
        return EXIT_CAPTURE_FAILED

    out_path = Path(args.out)
    if not out_path.is_file():
        print(f"shot.py: tool reported success but {out_path} does not exist", file=sys.stderr)
        return EXIT_CAPTURE_FAILED

    if args.json:
        sys.stdout.write(proc.stdout)
    else:
        print(out_path.resolve())
    # Surface page warnings (overflow, page errors) without failing the capture.
    if proc.stderr.strip():
        sys.stderr.write(proc.stderr)
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(EXIT_CAPTURE_FAILED)
