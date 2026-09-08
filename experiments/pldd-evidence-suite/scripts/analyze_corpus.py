#!/usr/bin/env python3
"""Generate the pinned corpus baseline and structural-hypothesis reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.analysis import baseline_report
from voynich.ivtff import parse_ivtff


def render_markdown(report: dict) -> str:
    integrity = report["integrity"]
    tokens = report["conservative_basic_eva"]
    hypothesis = report["hypotheses"]["H001"]
    feature = hypothesis["literature_derived_feature"]
    h002 = report["hypotheses"]["H002"]
    h002_audit = h002.get("cross_transcription_sta1_audit")
    h003 = report["hypotheses"].get("H003")
    lines = [
        "# Voynich corpus baseline",
        "",
        "> This is a transcription-structure report, not a decipherment or translation.",
        "",
        "## Source integrity",
        "",
        f"- SHA-256: `{integrity['source_sha256']}`",
        f"- Original source bytes retained: `{str(integrity['source_bytes_retained']).lower()}`",
        f"- IVTFF page/panel records / loci: {integrity['page_panel_records']} / {integrity['loci']}",
        f"- Locus families P/L/C/R: "
        f"{integrity['locus_families']['P']}/"
        f"{integrity['locus_families']['L']}/"
        f"{integrity['locus_families']['C']}/"
        f"{integrity['locus_families']['R']}",
        f"- Paragraph starts / ends: {integrity['paragraph_starts']} / {integrity['paragraph_ends']}",
        f"- Tokens with comma as boundary / joined: "
        f"{integrity['tokens_comma_as_boundary']} / {integrity['tokens_comma_joined']}",
        "",
        "## Conservative basic-EVA view",
        "",
        f"Accepted {tokens['accepted_tokens']} tokens of {tokens['types']} types. "
        f"Excluded {tokens['excluded_components']} uncertain or extended components.",
        "",
        "| Token | Count |",
        "|---|---:|",
    ]
    lines.extend(
        f"| `{item['token']}` | {item['count']} |" for item in tokens["top_tokens"][:20]
    )
    lines.extend(
        [
            "",
            "## H001: paragraph-initial positional enrichment",
            "",
            "H001 tests only whether specific transcribed forms are enriched at paragraph starts. "
            "It assigns no meaning or phonetic value.",
            "",
            f"Discovery pages: {hypothesis['discovery_pages']}; held-out pages: "
            f"{hypothesis['held_out_pages']}.",
            "",
            "The literature-derived feature is an accepted basic-EVA token beginning with "
            "`k`, `t`, `p`, or `f` (the conventional gallows forms).",
            "",
            "| Split | Initial feature rate | Background feature rate | Log2 odds |",
            "|---|---:|---:|---:|",
            f"| Discovery | {feature['discovery']['initial_rate']:.2%} | "
            f"{feature['discovery']['background_rate']:.2%} | "
            f"{feature['discovery']['log2_odds']} |",
            f"| Held out | {feature['held_out']['initial_rate']:.2%} | "
            f"{feature['held_out']['background_rate']:.2%} | "
            f"{feature['held_out']['log2_odds']} |",
            "",
            "The whole-token rows below are exploratory candidates, selected only in discovery "
            f"with: {hypothesis['exploratory_selection_rule']}. The frozen directional screen "
            "requires an observed held-out initial occurrence; smoothing alone does not count. "
            "This is descriptive, not inferential or an independent replication.",
            "",
            "| EVA token | Discovery total | Discovery initial | Discovery log2 odds | "
            "Held-out total | Held-out initial | Held-out log2 odds | Positive held-out direction |",
            "|---|---:|---:|---:|---:|---:|---:|:---:|",
        ]
    )
    for item in hypothesis["exploratory_whole_token_candidates"]:
        lines.append(
            f"| `{item['token']}` | {item['discovery_total']} | "
            f"{item['discovery_initial']} | {item['discovery_log2_odds']} | "
            f"{item['held_out_total']} | {item['held_out_initial']} | "
            f"{item['held_out_log2_odds']} | "
            f"{'yes' if item['held_out_direction_positive'] else 'no'} |"
        )
    if not hypothesis["exploratory_whole_token_candidates"]:
        lines.append("| _none_ |  |  |  |  |  |  | no |")
    lines.extend(
        [
            "",
            "Interpretation boundary: positional enrichment may reflect layout, scribal convention, "
            "morphology, a cipher mechanism, or grammar. It is not enough to gloss a token.",
            "",
            "## H002: local label-to-prose recurrence",
            "",
            "H002 tests whether exact certain-EVA types in true label loci recur in prose on "
            "the same page above a same-section, same-Currier, same-hand peer-page expectation.",
            "",
            "| Split | Pages | Label types | Observed local hits | Expected peer hits | Enrichment |",
            "|---|---:|---:|---:|---:|---:|",
            f"| Discovery | {h002['discovery']['pages_with_peers']} | "
            f"{h002['discovery']['evaluated_label_types']} | "
            f"{h002['discovery']['observed_local_hits']} | "
            f"{h002['discovery']['expected_peer_hits']} | "
            f"{h002['discovery']['enrichment']:.2%} |",
            f"| Held out | {h002['held_out']['pages_with_peers']} | "
            f"{h002['held_out']['evaluated_label_types']} | "
            f"{h002['held_out']['observed_local_hits']} | "
            f"{h002['held_out']['expected_peer_hits']} | "
            f"{h002['held_out']['enrichment']:.2%} |",
            "",
            f"Primary criterion: {h002['primary_criterion']}. Within-ZL numeric screen: "
            f"{'met' if h002['within_zl_primary_criterion_met'] else 'not met'}.",
            "",
            f"Held-out evaluation unit: {h002['held_out_evaluation_units']['unit']}; "
            f"count: {h002['held_out_evaluation_units']['count']}. "
            "This is a descriptive within-ZL screen, not an inferential result. "
            "Independent-transcription validation is required before using any hit as a crib.",
            "",
        ]
    )
    if h002_audit is not None:
        summary = h002_audit["summary"]
        lines.extend(
            [
                "### H002 cross-transcription STA1 audit",
                "",
                f"The positional audit mapped {summary['held_out_hits_audited']} held-out "
                "EVA hits into both ZL and GC STA1. "
                f"{summary['hits_with_exact_member_support_in_both_transcriptions']} retained "
                "exact member-level label/prose identity in both transcriptions; "
                f"{summary['hits_with_family_support_in_both_transcriptions']} retained "
                "family-level identity.",
                "",
                "| EVA token | Exact member identity in both | Family identity in both |",
                "|---|:---:|:---:|",
            ]
        )
        for hit in h002_audit["hits"]:
            lines.append(
                f"| `{hit['eva_token']}` | "
                f"{'yes' if hit['any_pair_exact_member_supported_by_both_transcriptions'] else 'no'} | "
                f"{'yes' if hit['any_pair_family_supported_by_both_transcriptions'] else 'no'} |"
            )
        lines.extend(
            [
                "",
                "Neither exact-EVA hit is supported as an exact member-level recurrence by "
                "both transcriptions. Do not advance either as a translation crib. The looser "
                "family-level survival motivated the retrospective H003 screen below.",
                "",
            ]
        )
    if h003 is not None:
        overlap = h003["prior_h002_partition_overlap"]
        lines.extend(
            [
                "## H003: locus-shared family-level label recurrence",
                "",
                "H003 retrospectively screens STA glyph-family types present in both ZL and GC "
                "at the same aligned locus. It uses unordered locus-level set "
                "intersection, not positional word agreement.",
                "",
                "| Partition | Pages | Label types | Observed local hits | Expected peer hits | Enrichment |",
                "|---|---:|---:|---:|---:|---:|",
                f"| Partition A | {h003['partition_a']['pages_with_peers']} | "
                f"{h003['partition_a']['evaluated_label_types']} | "
                f"{h003['partition_a']['observed_local_hits']} | "
                f"{h003['partition_a']['expected_peer_hits']} | "
                f"{h003['partition_a']['enrichment']:.2%} |",
                f"| Partition B | {h003['partition_b']['pages_with_peers']} | "
                f"{h003['partition_b']['evaluated_label_types']} | "
                f"{h003['partition_b']['observed_local_hits']} | "
                f"{h003['partition_b']['expected_peer_hits']} | "
                f"{h003['partition_b']['enrichment']:.2%} |",
                "",
                f"Partition validity: {h003['partition_validity']}.",
                f"All {len(overlap['partition_b_pages_with_peers'])} partition-B pages with "
                f"peers were already H002 discovery pages; "
                f"{len(overlap['also_h002_held_out_pages'])} were untouched H002 held-out pages.",
                "",
                f"Frozen advancement criterion: {h003['frozen_advancement_criterion']}.",
                f"Advancement result: "
                f"{'met' if h003['advancement_criterion_met'] else 'not met'}. "
                f"Disposition: {h003['disposition']}.",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/raw/transcriptions/ZL3b-n.txt",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=ROOT / "results/baseline-zl3b.json",
    )
    parser.add_argument(
        "--zl-sta",
        type=Path,
        default=ROOT / "data/raw/transcriptions/sta1/ZL3b.txt",
    )
    parser.add_argument(
        "--gc-sta",
        type=Path,
        default=ROOT / "data/raw/transcriptions/sta1/GC2a_0.txt",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=ROOT / "results/baseline-zl3b.md",
    )
    args = parser.parse_args()

    report = baseline_report(
        parse_ivtff(args.input.read_bytes()),
        zl_sta_document=parse_ivtff(args.zl_sta.read_bytes()),
        gc_sta_document=parse_ivtff(args.gc_sta.read_bytes()),
    )
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")


if __name__ == "__main__":
    main()
