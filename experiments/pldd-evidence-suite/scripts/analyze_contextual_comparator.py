#!/usr/bin/env python3
"""Generate the frozen H004-B-v2 contextual-comparator artifacts."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.contextual_comparator import (
    render_h004b2_markdown,
    run_h004b2_contextual_comparator,
)
from voynich.ivtff import parse_ivtff


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path, default=ROOT / "data/raw/transcriptions/ZL3b-n.txt"
    )
    parser.add_argument(
        "--h004a", type=Path, default=ROOT / "results/h004-local-order.json"
    )
    parser.add_argument(
        "--json", type=Path, default=ROOT / "results/h004b2-contextual-comparator.json"
    )
    parser.add_argument(
        "--markdown", type=Path, default=ROOT / "results/h004b2-contextual-comparator.md"
    )
    args = parser.parse_args()

    h004a_bytes = args.h004a.read_bytes()
    started = perf_counter()
    report = run_h004b2_contextual_comparator(
        parse_ivtff(args.input.read_bytes()),
        json.loads(h004a_bytes),
        h004a_report_sha256=sha256(h004a_bytes).hexdigest(),
        progress=lambda message: print(message, flush=True),
    )
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(render_h004b2_markdown(report), encoding="utf-8")
    elapsed = perf_counter() - started
    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")
    print(f"runtime_seconds={elapsed:.3f}")


if __name__ == "__main__":
    main()
