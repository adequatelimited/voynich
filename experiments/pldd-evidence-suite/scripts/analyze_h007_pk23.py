#!/usr/bin/env python3
"""Generate the frozen H007-PK23-COV-v1 coverage artifacts.

The wrapper exposes no key, table-repair, decoder-mode, exception-budget, or
output-release option.  Corpus inventory is verified before the author table
is loaded, and discovery gates programmatically seal holdout evaluation.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.naibbe_coverage import (
    build_h007_report,
    canonical_json_bytes,
    render_h007_markdown,
    render_sha256_sidecar,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen H007 published Naibbe-key coverage screen"
    )
    parser.add_argument(
        "--protocol",
        type=Path,
        default=ROOT / "notes/hypotheses/H007-PK23-published-key-coverage.md",
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
        "--vendor-root",
        type=Path,
        default=ROOT / "data/raw/external/naibbe-f2675ec",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=ROOT / "results/h007-pk23-coverage.json",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=ROOT / "results/h007-pk23-coverage.md",
    )
    parser.add_argument(
        "--sha256",
        type=Path,
        default=ROOT / "results/h007-pk23-coverage.sha256.txt",
    )
    args = parser.parse_args()

    report = build_h007_report(
        args.protocol,
        args.zl,
        args.it,
        args.vendor_root,
        ROOT,
    )
    report_bytes = canonical_json_bytes(report)
    report_hash = sha256(report_bytes).hexdigest()
    markdown = render_h007_markdown(report, report_hash)
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
