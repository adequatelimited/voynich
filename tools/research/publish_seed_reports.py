"""Derive human-readable seed reports and folio index from retained actual run outputs."""
import collections
import json
from pathlib import Path
import re
from engine import parse_ivtff

ROOT = Path(__file__).resolve().parents[2]


def save(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    compare_path = "experiments/comparisons/launch-seed-v1.json"
    comparison = json.loads((ROOT / compare_path).read_text())
    outputs = {}
    for path in sorted((ROOT / "experiments/runs/launch-seed-v1").glob("*/output.json")):
        output = json.loads(path.read_text())
        outputs[output["variant"]] = (path.relative_to(ROOT).as_posix(), output)
    zl = parse_ivtff(ROOT / "data/corpora/ZL3b-n.txt")
    gc = parse_ivtff(ROOT / "data/corpora/GC2a-n.txt")
    perpage = collections.Counter(l["page"] for l in zl["loci"])
    observed_folios = {int(m.group(1)) for p in zl["pages"] if (m := re.match(r"f(\d+)", p))}
    sides = {m.group(1) for p in zl["pages"] if (m := re.match(r"(f\d+[rv])", p))}
    missing = [12, 59, 60, 61, 62, 63, 64, 74, 91, 92, 97, 98, 109, 110]
    save("data/derived/folio-index.json", {"schema_version": "1.0", "source_id": "zl3b", "source_sha256": zl["sha256"], "id_policy": "Preserve IVTFF page/locus IDs. fRos is a multi-panel drawing spanning f85v/f86r; suffix digits denote panel conventions, not separate leaves.", "counts": {"custodian_physical_leaves": 102, "ZL_transcription_page_units": len(zl["pages"]), "GC_transcription_page_units": len(gc["pages"]), "ZL_numeric_folio_ids_observed": len(observed_folios), "ZL_numeric_side_ids_observed_excluding_fRos": len(sides), "ZL_units_with_numeric_panel_suffix": sum(bool(re.match(r"f\d+[rv]\d+$", p)) for p in zl["pages"]), "official_scan_count": None}, "missing_numbered_leaves": missing, "missing_leaf_source": "yale-catalog; IVTFF 2.0 foliation conventions", "rights": "Original index metadata: CC BY 4.0. ZL label source: hosted CC0 transliteration.", "image_mapping_status": "Official object HTTP 403 on 2026-09-06. No individual IIIF canvas IDs or scan counts invented.", "pages": [{"id": p, "title": p, "locus_count_ZL": perpage[p], "loci": [l["id"] for l in zl["loci"] if l["page"] == p], "source_specific_variables": entry["variables"], "present_in_GC": p in gc["pages"], "official_catalog_url": "https://collections.library.yale.edu/catalog/2002046", "physical_description_url": "https://pre1600ms.beinecke.library.yale.edu/docs/pre1600.ms408.HTM", "verified_canvas_id": None} for p,entry in zl["pages"].items()]})
    definitions = {
        "integrity": ("Corpus coverage and uncertainty audit", "corpus-integrity", "method-parse", "All 5,385 ZL loci parsed; 227 ZL page units versus 226 GC page units. GC lacks a page record for f116v. Counts refer to readings, not physical scans."),
        "frequency": ("Encoded-symbol frequency and token-length baselines", "statistical-structure", "method-frequency", "Full paragraph-token distributions and equal-token comparison with English prose, authored plaintext, symbol shuffles and copy/mutate pseudotext."),
        "entropy": ("Conditional symbol entropy under declared encodings", "statistical-structure", "method-entropy", "Empirical next-symbol entropy is compared at equal symbol counts; word-boundary inclusion is a separately labeled sensitivity analysis."),
        "position": ("Locus-position and repetition baselines", "statistical-structure", "method-position", "First-token lengths and adjacent repetition on P0 loci are compared to 39 within-locus token shuffles for each normalization variant."),
        "clustering": ("Source-label association and confounded clustering baseline", "layout-paleography", "method-cluster", "Unsupervised encoded-symbol page clusters are compared with ZL section and hand annotations; global and within-quire permutations expose confounding limits."),
    }
    for key, (title, branch, method, summary) in definitions.items():
        save(f"experiments/baselines/{key}.json", {"schema_version": "1.0", "id": f"baseline-{key}-v1", "title": title, "summary": summary, "status": "executed_descriptive_seed_baseline", "branch_ids": [branch], "method_ids": [method], "family_id": f"seed-baseline-{key}", "protocol": "protocols/launch-seed-v1.json", "protocol_sha256": comparison["protocol_sha256"], "registration_status": "Descriptive launch baseline, frozen locally after a join-variant engineering smoke run; not preregistered confirmatory science.", "comparison": compare_path, "outputs": [{"variant": variant, "path": path, "json_pointer": f"/{key}"} for variant,(path,_) in outputs.items()], "report": f"experiments/baselines/{key}.md", "inputs": ["data/manifests/zl3b.json", "data/manifests/alice-english.json"], "controls": ["meaningful English Alice prose", "authored known-plaintext templates", "equal-length symbol shuffle", "authored bounded copy/mutate pseudotext", "type-appropriate positional/label permutations"], "independent_human_reproduction": "pending", "seed": True, "competitive_points": 0, "limitations": ["These are descriptive instrument baselines, not new language identifications or translation claims.", "Source-specific labels and encoded units remain uncertain; all three registered variants are retained."]})
        text = f"# {title}\n\n{summary}\n\nStatus: **actually executed; descriptive seed; zero competitive points**. Python 3.14 standard library; seed 408. The local protocol was frozen after an engineering smoke run had already inspected the join variant. It is not independent preregistration. No search for a best variant occurred; all join, split and strict runs are published.\n\n"
        text += "Reproduce the complete suite with the commands in [the harness guide](../../tools/research/README.md). Exact source hashes, code hashes, commands, elapsed/CPU time and raw outputs are in [the protocol](../../protocols/launch-seed-v1.json), [comparison](../comparisons/launch-seed-v1.json) and referenced run manifests.\n\n"
        text += "| Variant | Retained paragraph tokens | Mean encoded token length | Conditional bits/symbol | Section NMI | Source-hand NMI |\n|---|---:|---:|---:|---:|---:|\n"
        for row in comparison["summaries"]:
            text += f'| {row["variant"]} | {row["retained_paragraph_tokens"]:,} | {row["mean_token_length"]:.5f} | {row["conditional_entropy"]:.5f} | {row["section_nmi"]:.5f} | {row["source_specific_hand_nmi"]:.5f} |\n'
        text += "\nThis common table locates the result within the shared sensitivity study; each file's output pointer identifies its actual full diagnostics. Conditional entropy is a plug-in estimator within tokens at matched symbol count, not the whole-corpus average or a translation score.\n\n"
        for variant,(path,out) in outputs.items():
            text += f"## {variant}\n\nFull output: [{path}]({Path('../..').joinpath(path).as_posix()}), JSON member `{key}`.\n\n"
            if key == "integrity":
                result = out[key]
                text += f'Parsed {result["loci"]:,} loci, including {result["paragraph_loci"]:,} paragraph-type loci. Normalization retained {result["normalization"]["accepted_tokens"]:,} tokens across all loci and excluded {result["normalization"].get("excluded_tokens",0):,}; paragraph statistics use {result["paragraph_tokens_retained"]:,}. There are {result["raw_alternative_reading_groups"]} alternative-reading groups and {result["raw_uncertain_spaces"]:,} uncertain-space markers in locus data.\n\n'
            elif key == "frequency":
                result = out[key]
                text += f'The full paragraph scope contains {result["actual_full_paragraph_corpus"]["types"]:,} retained token types. Each comparison uses the first {result["matched_token_count"]:,} tokens in its declared sequence. Full symbol counts, top token counts and length histograms are retained in JSON; the shuffled control conserves both token lengths and total symbol counts.\n\n'
            elif key == "entropy":
                result = out[key]
                text += f'The comparison uses {result["matched_symbol_count_without_boundaries"]:,} encoded symbols per input. Empirical conditional entropy: ' + "; ".join(f'{name} {value["next_symbol_given_previous_bits"]:.5f} bits' for name,value in result["comparison"].items()) + ".\n\n"
            elif key == "position":
                result = out[key]["actual"]
                text += f'The retained scope contains {result["eligible_loci"]:,} P0 loci of at least two tokens. The first-token minus nonfirst-token mean length is {result["first_minus_nonfirst_mean_length"]:.5f} encoded symbols; adjacent repeat rate is {result["adjacent_repeat_rate"]:.6f}. The raw 39 shuffle values and finite tail diagnostic are included; no corrected significance or causal conclusion is asserted.\n\n'
            else:
                result = out[key]
                text += f'Clusters use {result["pages"]} page units and k={result["k"]}. Section NMI is {result["section_nmi"]["observed"]:.5f}; the global-shuffle mean is {result["section_nmi"]["null_mean"]:.5f} and within-quire-shuffle mean {result["within_quire_section_nmi"]["null_mean"]:.5f}. Hand NMI uses {result["single_hand_labeled_pages"]} pages with a single ZL H label; {result["excluded_mixed_or_unknown_hand_pages"]} mixed/unknown cases are excluded.\n\n'
        text += "## Limits and next evidence\n\nEVA encodes shapes: its characters, apostrophes and atomic rare-symbol codes are analytical units, not recovered graphemes or phonemes. Unreadable/unsupported tokens are excluded; join and split select the first source alternative, while strict excludes ambiguous tokens. Drawing interruptions become apparent spaces. Subtype P0 loci need not equal physical manuscript lines.\n\nThe English comparison is a fixed prefix of one prose work; authored and copied/mutated controls test limited failure modes, not the space of all languages or historical mechanisms. Clustering uses one fixed initialization and source-specific metadata with strong potential quire/section/hand dependence. No independent human reproduction, image-based corpus validation or external scholarly endorsement is claimed.\n"
        (ROOT / f"experiments/baselines/{key}.md").write_text(text, encoding="utf-8")
    print(json.dumps({"baseline_reports": 5, "page_index_units": len(zl["pages"]), "variants": len(outputs)}))


if __name__ == "__main__":
    main()
