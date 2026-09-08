#!/usr/bin/env python3
"""Generate the frozen H005-v1 pre-IT ZL/GC artifacts."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.ivtff import parse_ivtff
from voynich.plant_anchors import (
    build_h005_report,
    canonical_json_bytes,
    render_h005_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen H005 ZL/GC plant-anchor screen without IT"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data/derived/h005-source-anchor-manifest.json",
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        default=ROOT / "notes/hypotheses/H005-pharmaceutical-plant-anchors.md",
    )
    parser.add_argument(
        "--eva",
        type=Path,
        default=ROOT / "data/raw/transcriptions/ZL3b-n.txt",
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
        "--json",
        type=Path,
        default=ROOT / "results/h005-plant-anchors.json",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=ROOT / "results/h005-plant-anchors.md",
    )
    parser.add_argument(
        "--sha256",
        type=Path,
        default=ROOT / "results/h005-plant-anchors.sha256.txt",
    )
    args = parser.parse_args()

    manifest_bytes = args.manifest.read_bytes()
    protocol_bytes = args.protocol.read_bytes()
    report = build_h005_report(
        manifest_bytes,
        protocol_bytes,
        parse_ivtff(args.eva.read_bytes()),
        parse_ivtff(args.zl.read_bytes()),
        parse_ivtff(args.gc.read_bytes()),
    )
    report["inputs"]["source_anchor_manifest"]["path"] = str(
        args.manifest.resolve().relative_to(ROOT)
    )
    report["inputs"]["protocol"]["path"] = str(args.protocol.resolve().relative_to(ROOT))
    report["inputs"]["eva"]["path"] = str(args.eva.resolve().relative_to(ROOT))
    report["inputs"]["zl_sta1"]["path"] = str(args.zl.resolve().relative_to(ROOT))
    report["inputs"]["gc_sta1"]["path"] = str(args.gc.resolve().relative_to(ROOT))

    report_bytes = canonical_json_bytes(report)
    report_hash = sha256(report_bytes).hexdigest()
    markdown = render_h005_markdown(report, report_hash)

    for path in (args.json, args.markdown, args.sha256):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_bytes(report_bytes)
    args.markdown.write_text(markdown, encoding="utf-8")
    args.sha256.write_text(
        f"{report_hash}  {args.json.name}\n", encoding="ascii"
    )

    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")
    print(f"wrote {args.sha256}")
    print(f"report SHA-256 {report_hash}")


if __name__ == "__main__":
    main()
