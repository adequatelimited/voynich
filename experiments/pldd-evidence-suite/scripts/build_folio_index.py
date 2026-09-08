#!/usr/bin/env python3
"""Build a verbatim Yale-canvas index without guessing foldout mappings."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.iiif import load_canvases, serializable_index
from voynich.ivtff import parse_ivtff


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data/raw/iiif/yale-ms-408.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/derived/yale-canvas-index.json",
    )
    parser.add_argument(
        "--transcription",
        type=Path,
        default=ROOT / "data/raw/transcriptions/ZL3b-n.txt",
    )
    args = parser.parse_args()

    document = parse_ivtff(args.transcription.read_bytes())
    valid_page_ids = {page.page_id for page in document.pages}
    index = serializable_index(load_canvases(args.manifest), valid_page_ids)
    index["schema_version"] = 1
    index["generator"] = "scripts/build_folio_index.py"
    index["sources"] = {
        "manifest": {
            "url": "https://collections.library.yale.edu/manifests/2002046",
            "retrieved": "2026-07-09",
            "sha256": sha256(args.manifest.read_bytes()).hexdigest(),
        },
        "valid_page_ids": {
            "path": "data/raw/transcriptions/ZL3b-n.txt",
            "sha256": sha256(args.transcription.read_bytes()).hexdigest(),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({index['canvas_count']} canvases)")


if __name__ == "__main__":
    main()
