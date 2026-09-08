#!/usr/bin/env python3
"""Generate the isolated P001 edge-morphology pilot artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.edge_morphology import analyze_edge_morphology
from voynich.ivtff import parse_ivtff


def render_markdown(report: dict) -> str:
    partitions = report["partitions"]
    calibration = report["evaluation"]["calibration"]
    test = report["evaluation"]["test"]
    control = report["equal_cardinality_control"]
    selection = report["selection"]
    lines = [
        "# P001: atomic edge-slot morphology pilot",
        "",
        "> Failed discriminating-control pilot. This is not a decipherment or translation.",
        "",
        "## Validity boundary",
        "",
        report["protocol_status"] + ".",
        "",
        report["split"]["disclosure"] + ".",
        "",
        "## Frozen scratch calculation",
        "",
        f"- Split tag: `{report['split']['tag']}`.",
        "- Unit: strict certain-space `P*` STA1 family word.",
        f"- Selected prefix family: `{selection['selected_prefix_families'][0]}`.",
        "- Selected suffix families: "
        + ", ".join(f"`{item}`" for item in selection["selected_suffix_families"])
        + ".",
        "- Parse: optional one-family prefix, nonempty core, optional one-family suffix.",
        "",
        "| Partition | Pages | Tokens | Family types |",
        "|---|---:|---:|---:|",
    ]
    for name in ("train", "calibration", "test"):
        item = partitions[name]
        lines.append(
            f"| {name.title()} | {item['pages_with_accepted_prose_words']} | "
            f"{item['accepted_tokens']} | {item['family_types']} |"
        )
    lines.extend(
        [
            "",
            "## Productive recombination",
            "",
            "A productive type is unseen as a surface type, has at least one selected edge "
            "family, and recombines a training-seen core into a training-unseen slot tuple.",
            "",
            "| Partition | Productive / unseen affixed types | Rate | Coverage of all unseen types |",
            "|---|---:|---:|---:|",
            f"| Calibration | {calibration['productive_unseen_types']} / "
            f"{calibration['unseen_affixed_types']} | "
            f"{calibration['productive_type_rate_among_affixed']:.2%} | "
            f"{calibration['productive_type_coverage_all_unseen']:.2%} |",
            f"| Test | {test['productive_unseen_types']} / "
            f"{test['unseen_affixed_types']} | "
            f"{test['productive_type_rate_among_affixed']:.2%} | "
            f"{test['productive_type_coverage_all_unseen']:.2%} |",
            "",
            "## Equal-cardinality control",
            "",
            f"The exhaustive control contains {control['equal_cardinality_inventories']:,} "
            "one-prefix/two-suffix inventories over the training alphabet, including the "
            "selected inventory. "
            f"{control['inventories_with_strictly_higher_test_rate']:,} inventories had a "
            "strictly higher test productive-type rate.",
            "",
            f"Selected-inventory rank: {control['selected_inventory_rank_from_best']:,} of "
            f"{control['equal_cardinality_inventories']:,}; percentile "
            f"{control['selected_inventory_percentile']:.2%}. The advancement gate was "
            f"{control['advancement_percentile_gate']:.0%}.",
            "",
            "## Disposition",
            "",
            report["advancement"]["disposition"].capitalize() + ".",
            "",
            "The observed recombination is descriptive but not distinctive: arbitrary "
            "equal-cardinality edge inventories commonly perform as well or better. No "
            "STA family, core, or surface form receives a semantic or phonetic value.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/raw/transcriptions/sta1/ZL3b.txt",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=ROOT / "results/p001-edge-morphology.json",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=ROOT / "results/p001-edge-morphology.md",
    )
    args = parser.parse_args()

    report = analyze_edge_morphology(parse_ivtff(args.input.read_bytes()))
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")


if __name__ == "__main__":
    main()
