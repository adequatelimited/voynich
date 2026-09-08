#!/usr/bin/env python3
"""Generate the frozen H004-C pre-IT ZL/GC discovery artifacts.

There is intentionally no IT command-line argument or file access in this
entry point.  The reserved IT hash is copied from the frozen protocol only.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.h004c import (
    build_discovery_manifest,
    canonical_manifest_bytes,
    render_zg_discovery_markdown,
)
from voynich.ivtff import parse_ivtff


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run only the frozen H004-C ZL/GC discovery stage"
    )
    parser.add_argument(
        "--zl",
        type=Path,
        default=ROOT / "data/raw/transcriptions/sta1/ZL3b.txt",
    )
    parser.add_argument(
        "--gc",
        type=Path,
        default=ROOT / "data/raw/transcriptions/sta1/GC2a_0.txt",
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        default=ROOT / "notes/hypotheses/H004C-cross-transcription-sta.md",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=ROOT / "results/h004c-zg-discovery-manifest.json",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=ROOT / "results/h004c-zg-discovery.md",
    )
    parser.add_argument(
        "--sha256",
        type=Path,
        default=ROOT / "results/h004c-zg-discovery-manifest.sha256.txt",
    )
    args = parser.parse_args()

    protocol_bytes = args.protocol.read_bytes()
    protocol_text = protocol_bytes.decode("utf-8")
    manifest = build_discovery_manifest(
        parse_ivtff(args.zl.read_bytes()),
        parse_ivtff(args.gc.read_bytes()),
        protocol_text=protocol_text,
        protocol_path=str(args.protocol.resolve().relative_to(ROOT)),
    )
    manifest["inputs"]["zl_sta1"]["path"] = str(args.zl.resolve().relative_to(ROOT))
    manifest["inputs"]["gc_sta1_level0"]["path"] = str(args.gc.resolve().relative_to(ROOT))

    manifest_bytes = canonical_manifest_bytes(manifest)
    manifest_hash = sha256(manifest_bytes).hexdigest()
    markdown = render_zg_discovery_markdown(manifest, manifest_hash)

    for path in (args.json, args.markdown, args.sha256):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_bytes(manifest_bytes)
    args.markdown.write_text(markdown, encoding="utf-8")
    args.sha256.write_text(
        f"{manifest_hash}  {args.json.name}\n",
        encoding="ascii",
    )

    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")
    print(f"wrote {args.sha256}")
    print(f"manifest SHA-256 {manifest_hash}")


if __name__ == "__main__":
    main()
