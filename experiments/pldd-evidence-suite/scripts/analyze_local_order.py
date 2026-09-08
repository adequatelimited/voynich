#!/usr/bin/env python3
"""Generate the isolated H004 local-order report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.ivtff import parse_ivtff
from voynich.local_order import render_h004_markdown, run_h004_local_order


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path, default=ROOT / "data/raw/transcriptions/ZL3b-n.txt"
    )
    parser.add_argument(
        "--json", type=Path, default=ROOT / "results/h004-local-order.json"
    )
    parser.add_argument(
        "--markdown", type=Path, default=ROOT / "results/h004-local-order.md"
    )
    parser.add_argument("--permutations", type=int, default=9999)
    parser.add_argument("--seed", type=int, default=4004)
    args = parser.parse_args()

    report = run_h004_local_order(
        parse_ivtff(args.input.read_bytes()),
        permutations=args.permutations,
        seed=args.seed,
    )
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(render_h004_markdown(report), encoding="utf-8")
    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")


if __name__ == "__main__":
    main()
