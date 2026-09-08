"""Frozen H004-v1 local-order screen for conservative basic-EVA prose.

This module tests sequential near-edit clustering against a constrained static
null.  It does not test, identify, or validate a copy/edit generator.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import random
import statistics
from typing import Any

from .ivtff import Document, iter_paragraphs, tokenize_certain_basic_eva


Stratum = tuple[str, str, str]
CellKey = tuple[Stratum, int, bool, str]


@dataclass(frozen=True)
class Target:
    position: int
    context: tuple[int, ...]
    stratum: Stratum


@dataclass(frozen=True)
class LocalOrderPage:
    page_id: str
    tokens: tuple[str, ...]
    cells: tuple[tuple[CellKey, tuple[int, ...]], ...]
    targets: tuple[Target, ...]
    runs: tuple[tuple[int, ...], ...]


@lru_cache(maxsize=None)
def edit_distance_class(left: str, right: str) -> int:
    """Return 0, 1, or 2, where 2 means edit distance greater than one."""

    if left == right:
        return 0
    if abs(len(left) - len(right)) > 1:
        return 2
    if len(left) == len(right):
        return 1 if sum(a != b for a, b in zip(left, right)) == 1 else 2
    if len(left) > len(right):
        left, right = right, left
    # ``right`` is one character longer.  At most one skipped character is
    # allowed; substitution plus insertion therefore fails closed.
    i = j = 0
    skipped = False
    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            i += 1
            j += 1
        elif skipped:
            return 2
        else:
            skipped = True
            j += 1
    return 1


def _line_position(index: int, count: int) -> str:
    if count == 1:
        return "singleton"
    if index == 0:
        return "first"
    if index == count - 1:
        return "last"
    return "middle"


def build_local_order_pages(
    document: Document,
    *,
    window: int = 10,
    include_pages_without_targets: bool = False,
) -> tuple[LocalOrderPage, ...]:
    """Build H004 sequences; uncertainty and metadata changes reset context."""

    if document.header.alphabet != "Eva-":
        raise ValueError(f"H004 requires an Eva- IVTFF document; got {document.header.alphabet!r}")
    if window < 1:
        raise ValueError("window must be positive")

    mutable: dict[str, dict[str, Any]] = {
        page.page_id: {
            "tokens": [],
            "cells": defaultdict(list),
            "targets": [],
            "runs": [],
        }
        for page in document.pages
    }
    for paragraph in iter_paragraphs(document):
        record = mutable[paragraph.page_id]
        run: list[int] = []
        last_stratum: Stratum | None = None
        paragraph_component = 0

        def finish_run() -> None:
            if run:
                record["runs"].append(tuple(run))
                run.clear()

        for locus in paragraph.loci:
            if locus.locator == "!":
                finish_run()
                last_stratum = None
                continue
            stratum = tuple(
                locus.effective_variables.get(variable, "unknown") for variable in "ILH"
            )
            if stratum != last_stratum:
                finish_run()
                last_stratum = stratum
            components = tokenize_certain_basic_eva(locus.text).components
            for component_index, component in enumerate(components):
                paragraph_initial = paragraph_component == 0
                paragraph_component += 1
                if component.token is None or "unknown" in stratum:
                    finish_run()
                    continue
                position = len(record["tokens"])
                record["tokens"].append(component.token)
                cell: CellKey = (
                    stratum,
                    len(component.token),
                    paragraph_initial,
                    _line_position(component_index, len(components)),
                )
                record["cells"][cell].append(position)
                run.append(position)
                if len(run) > window:
                    record["targets"].append(
                        Target(position, tuple(run[-window - 1 : -1]), stratum)
                    )
        finish_run()

    return tuple(
        LocalOrderPage(
            page_id=page.page_id,
            tokens=tuple(mutable[page.page_id]["tokens"]),
            cells=tuple(
                (key, tuple(positions))
                for key, positions in mutable[page.page_id]["cells"].items()
            ),
            targets=tuple(mutable[page.page_id]["targets"]),
            runs=tuple(mutable[page.page_id]["runs"]),
        )
        for page in document.pages
        if include_pages_without_targets
        or mutable[page.page_id]["targets"]
    )


def _is_reserved(page_id: str) -> bool:
    return sha256(f"H004-v1:{page_id}".encode("ascii")).digest()[0] < 51


def _page_metrics(page: LocalOrderPage, tokens: tuple[str, ...] | list[str]) -> tuple[float, float, float]:
    copy_or_edit = mutation = exact = 0
    for target in page.targets:
        minimum = min(
            edit_distance_class(tokens[target.position], tokens[index])
            for index in target.context
        )
        copy_or_edit += minimum <= 1
        mutation += minimum == 1
        exact += minimum == 0
    total = len(page.targets)
    return copy_or_edit / total, mutation / total, exact / total


def _currier_metrics(
    pages: tuple[LocalOrderPage, ...], token_maps: dict[str, list[str]] | None = None
) -> dict[str, tuple[float, float, float, int]]:
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    for page in pages:
        tokens = page.tokens if token_maps is None else token_maps[page.page_id]
        for target in page.targets:
            minimum = min(
                edit_distance_class(tokens[target.position], tokens[index])
                for index in target.context
            )
            currier = target.stratum[1]
            counts[currier][0] += minimum <= 1
            counts[currier][1] += minimum == 1
            counts[currier][2] += minimum == 0
            counts[currier][3] += 1
    return {
        key: (value[0] / value[3], value[1] / value[3], value[2] / value[3], value[3])
        for key, value in counts.items()
    }


def _shuffle(pages: tuple[LocalOrderPage, ...], rng: random.Random) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for page in pages:
        tokens = list(page.tokens)
        for _, positions in page.cells:
            values = [tokens[index] for index in positions]
            rng.shuffle(values)
            for index, value in zip(positions, values):
                tokens[index] = value
        result[page.page_id] = tokens
    return result


def _metric_report(
    observed: float,
    null: list[float],
    page_observed: list[float],
    page_null_sums: list[float],
    *,
    delta_minimum: float = 0.02,
    p_maximum: float = 0.005,
) -> dict[str, Any]:
    null_mean = statistics.fmean(null)
    residuals = [
        value - page_null_sums[index] / len(null)
        for index, value in enumerate(page_observed)
    ]
    positive = sum(value > 0 for value in residuals)
    p_value = (1 + sum(value >= observed for value in null)) / (len(null) + 1)
    return {
        "observed_equal_page_mean": round(observed, 6),
        "null_mean": round(null_mean, 6),
        "delta": round(observed - null_mean, 6),
        "monte_carlo_p": round(p_value, 6),
        "positive_pages": positive,
        "zero_pages": sum(value == 0 for value in residuals),
        "negative_pages": sum(value < 0 for value in residuals),
        "positive_page_fraction": round(positive / len(residuals), 6),
        "gate_checks": {
            "delta_at_least_0_02": observed - null_mean >= delta_minimum,
            "p_at_most_0_005": p_value <= p_maximum,
            "positive_page_fraction_above_0_60": positive / len(residuals) > 0.60,
        },
    }


def run_h004_local_order(
    document: Document,
    *,
    permutations: int = 9999,
    seed: int = 4004,
    window: int = 10,
    minimum_page_targets: int = 10,
) -> dict[str, Any]:
    """Run the frozen H004-v1 held-out static matched-null screen."""

    if permutations < 1:
        raise ValueError("permutations must be positive")
    pages = build_local_order_pages(document, window=window)
    eligible = tuple(page for page in pages if len(page.targets) >= minimum_page_targets)
    reserved = tuple(page for page in eligible if _is_reserved(page.page_id))
    discovery = tuple(page for page in eligible if not _is_reserved(page.page_id))
    if not reserved:
        raise ValueError("H004 split produced no reserved pages")

    observed_rows = [_page_metrics(page, page.tokens) for page in reserved]
    observed = tuple(statistics.fmean(row[index] for row in observed_rows) for index in range(3))
    observed_currier = _currier_metrics(reserved)
    null: list[list[float]] = [[], [], []]
    page_null_sums = [[0.0, 0.0, 0.0] for _ in reserved]
    currier_null: dict[str, list[list[float]]] = {
        key: [[], [], []] for key in observed_currier
    }
    rng = random.Random(seed)
    for _ in range(permutations):
        token_maps = _shuffle(reserved, rng)
        rows = [_page_metrics(page, token_maps[page.page_id]) for page in reserved]
        for metric in range(3):
            null[metric].append(statistics.fmean(row[metric] for row in rows))
        for page_index, row in enumerate(rows):
            for metric in range(3):
                page_null_sums[page_index][metric] += row[metric]
        for currier, row in _currier_metrics(reserved, token_maps).items():
            for metric in range(3):
                currier_null[currier][metric].append(row[metric])

    names = ("copy_or_one_edit", "one_edit_without_exact", "exact_repeat_diagnostic")
    held_out_results = {
        name: _metric_report(
            observed[index],
            null[index],
            [row[index] for row in observed_rows],
            [row[index] for row in page_null_sums],
        )
        for index, name in enumerate(names)
    }

    currier_results: dict[str, Any] = {}
    for currier, values in sorted(observed_currier.items()):
        metrics: dict[str, Any] = {}
        for index, name in enumerate(names[:2]):
            distribution = currier_null[currier][index]
            mean = statistics.fmean(distribution)
            p_value = (1 + sum(value >= values[index] for value in distribution)) / (
                permutations + 1
            )
            metrics[name] = {
                "observed": round(values[index], 6),
                "null_mean": round(mean, 6),
                "delta": round(values[index] - mean, 6),
                "monte_carlo_p": round(p_value, 6),
                "robustness_check_met": values[index] > mean and p_value <= 0.025,
            }
        currier_results[currier] = {"targets": values[3], "metrics": metrics}

    reserved_target_count = sum(len(page.targets) for page in reserved)
    movable_targets = sum(
        target.position in {
            position
            for _, positions in page.cells
            if len({page.tokens[index] for index in positions}) > 1
            for position in positions
        }
        for page in reserved
        for target in page.targets
    )
    currier_pages = {
        currier: sum(
            any(target.stratum[1] == currier for target in page.targets) for page in reserved
        )
        for currier in ("A", "B")
    }
    breadth_checks = {
        "at_least_30_reserved_pages": len(reserved) >= 30,
        "at_least_1500_reserved_targets": reserved_target_count >= 1500,
        "currier_A_at_least_5_pages_and_200_targets": currier_pages["A"] >= 5
        and observed_currier.get("A", (0, 0, 0, 0))[3] >= 200,
        "currier_B_at_least_5_pages_and_200_targets": currier_pages["B"] >= 5
        and observed_currier.get("B", (0, 0, 0, 0))[3] >= 200,
        "movable_target_fraction_at_least_0_80": movable_targets / reserved_target_count >= 0.80,
    }
    primary_checks = [
        value
        for name in names[:2]
        for value in held_out_results[name]["gate_checks"].values()
    ]
    currier_checks = [
        data["robustness_check_met"]
        for result in currier_results.values()
        for data in result["metrics"].values()
    ]
    static_gate = all(breadth_checks.values()) and all(primary_checks) and all(currier_checks)

    return {
        "hypothesis_id": "H004",
        "analysis_version": "H004-v1",
        "claim_scope": "local transcription-form prediction beyond a static matched null; no semantics or generator claim",
        "input": {
            "source_sha256": sha256(document.source).hexdigest(),
            "alphabet": document.header.alphabet,
            "format_version": document.header.version,
        },
        "protocol": {
            "window_tokens": window,
            "minimum_page_targets": minimum_page_targets,
            "split": "SHA256('H004-v1:' + page_id), first byte < 51 is reserved",
            "permutations": permutations,
            "seed": seed,
            "distance": "EVA code-point Levenshtein thresholded at 0, 1, or >1",
            "null_cells": ["page", "I", "L", "H", "EVA_length", "paragraph_initial", "line_position"],
            "reset_conditions": ["paragraph boundary", "uncertain or excluded component", "I/L/H change"],
            "aggregation": "mean within page, then equal mean across pages",
        },
        "eligibility": {
            "pages_with_any_targets": len(pages),
            "eligible_discovery_pages": len(discovery),
            "eligible_reserved_pages": len(reserved),
            "discovery_targets": sum(len(page.targets) for page in discovery),
            "reserved_targets": reserved_target_count,
            "reserved_currier_pages": currier_pages,
            "reserved_currier_targets": {
                key: observed_currier.get(key, (0, 0, 0, 0))[3] for key in ("A", "B")
            },
            "movable_reserved_targets": movable_targets,
            "movable_reserved_target_fraction": round(movable_targets / reserved_target_count, 6),
        },
        "held_out_static_null": held_out_results,
        "held_out_currier_robustness": currier_results,
        "breadth_checks": breadth_checks,
        "static_matched_null_gate_met": static_gate,
        "mechanism_gate": {
            "copy_edit_mechanism_advanced": False,
            "reason": "the static order effect is compatible with Markov dependence, morphology, syntax, topic sequence, and transcription effects",
            "unimplemented_required_tests": [
                "discovery-trained order-1 and order-2 word-Markov surrogates",
                "cross-transcription STA-family robustness check",
            ],
        },
        "disposition": (
            "predictive-order screen passed; copy/edit mechanism remains unvalidated"
            if static_gate
            else "predictive-order screen did not pass the frozen gate"
        ),
    }


def render_h004_markdown(report: dict[str, Any]) -> str:
    """Render a compact human-readable H004 report."""

    eligibility = report["eligibility"]
    lines = [
        "# H004: local preceding-context screen",
        "",
        "> Structural transcription analysis only; this is not a translation or a validated copy/edit mechanism.",
        "",
        f"- Source SHA-256: `{report['input']['source_sha256']}`",
        f"- Reserved pages / targets: {eligibility['eligible_reserved_pages']} / {eligibility['reserved_targets']}",
        f"- Permutations / seed: {report['protocol']['permutations']} / {report['protocol']['seed']}",
        f"- Static matched-null gate: `{'met' if report['static_matched_null_gate_met'] else 'not met'}`",
        "",
        "| Metric | Observed | Null mean | Delta | Monte Carlo p | Positive pages |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    labels = {
        "copy_or_one_edit": "Exact or one edit",
        "one_edit_without_exact": "One edit, no exact",
        "exact_repeat_diagnostic": "Exact repeat (diagnostic)",
    }
    for key, label in labels.items():
        item = report["held_out_static_null"][key]
        lines.append(
            f"| {label} | {item['observed_equal_page_mean']:.4f} | "
            f"{item['null_mean']:.4f} | {item['delta']:+.4f} | "
            f"{item['monte_carlo_p']:.4g} | {item['positive_pages']} |"
        )
    lines.extend(
        [
            "",
            "The null preserves the exact page token multiset and shuffles only within "
            "I/L/H, EVA-length, paragraph-initial, and line-position cells.",
            "",
            f"Disposition: {report['disposition']}.",
            "",
            "A static-null pass is not evidence for copy/edit generation. Order-1/order-2 "
            "Markov surrogates and a cross-transcription STA-family robustness check are not implemented "
            "here and remain mandatory before any mechanism claim.",
        ]
    )
    return "\n".join(lines) + "\n"
