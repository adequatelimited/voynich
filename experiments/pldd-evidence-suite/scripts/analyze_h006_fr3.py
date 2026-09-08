#!/usr/bin/env python3
"""Generate the frozen H006-FR3-LINE-v1 frame-screen artifacts.

This entry point has no key, plaintext, dictionary, language-model, or gate
override arguments.  The module keeps holdout residues sealed unless exact
discovery qualification and frozen holdout breadth both authorize evaluation.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.ternary_frame import (
    build_h006_report,
    canonical_json_bytes,
    recorded_relative_path,
    render_h006_markdown,
    render_sha256_sidecar,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen key-independent H006 fixed-three-trit line-frame screen"
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        default=ROOT / "notes/hypotheses/H006-FR3-line-reset-ternary-code.md",
    )
    parser.add_argument(
        "--zl",
        type=Path,
        default=ROOT / "data/raw/transcriptions/ZL3b-n.txt",
    )
    parser.add_argument(
        "--it",
        type=Path,
        default=ROOT / "data/raw/transcriptions/IT2a-n.txt",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=ROOT / "results/h006-fr3-line-reset.json",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=ROOT / "results/h006-fr3-line-reset.md",
    )
    parser.add_argument(
        "--sha256",
        type=Path,
        default=ROOT / "results/h006-fr3-line-reset.sha256.txt",
    )
    args = parser.parse_args()

    report = build_h006_report(
        args.protocol.read_bytes(), args.zl.read_bytes(), args.it.read_bytes()
    )

    report["inputs"]["protocol"]["path"] = recorded_relative_path(
        args.protocol, ROOT
    )
    report["inputs"]["zl_eva"]["path"] = recorded_relative_path(args.zl, ROOT)
    report["inputs"]["it_eva"]["path"] = recorded_relative_path(args.it, ROOT)

    report_bytes = canonical_json_bytes(report)
    report_hash = sha256(report_bytes).hexdigest()
    markdown = render_h006_markdown(report, report_hash)
    sidecar = render_sha256_sidecar(report_hash, args.json.name)

    for path in (args.json, args.markdown, args.sha256):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_bytes(report_bytes)
    args.markdown.write_text(markdown, encoding="utf-8")
    args.sha256.write_text(sidecar, encoding="ascii")

    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")
    print(f"wrote {args.sha256}")
    print(f"report SHA-256 {report_hash}")


if __name__ == "__main__":
    main()
