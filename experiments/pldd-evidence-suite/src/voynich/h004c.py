"""Frozen H004-C-v1 pre-IT ZL/GC discovery analysis.

This module deliberately has no IT input or projection path.  It builds the
strict ordinal ZL/GC component skeleton, freezes exact ten-component contexts,
and evaluates the joint matched static-order null required before the reserved
IT witness may be projected.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
import math
import random
import re
import statistics
from typing import Any, Iterable

from .ivtff import Document, Locus
from .local_order import edit_distance_class


ANALYSIS_VERSION = "H004-C-v1"
STAGE = "pre-IT ZL/GC discovery"
WINDOW = 10
PERMUTATIONS = 9_999
SEED_LABEL = "H004-C-v1|ZG|seed=4004"
SEED = int.from_bytes(sha256(SEED_LABEL.encode("ascii")).digest()[:16], "big")

ZL_SHA256 = "8438ba1c45f47fe1d06b5262cbcdf60ce69158a0edbd4dd802612896f3217e2a"
GC_SHA256 = "b39cabbd9c8c8a098bfa9f76e0649291d17d77e1cb4fb0a3351ff7bdc832ace3"
DECLARED_RESERVED_IT_SHA256 = (
    "215f2d05690828c00bd4ae00d6201df31050adcd81601343b142ae91b9dfeee4"
)
IVTFF_SPEC_SHA256 = "7ac9c4a82064763cac8767cca6f661cc4e1b4503ab9342acc03032ddb6939d49"
STA1_SPEC_SHA256 = "85a595aa61936fa103a0f2c11d980e9970e11f98d1f35038f9fc268cc433ada2"

_INLINE_TAG_RE = re.compile(r"<[^>]*>")
_LIGATURE_RE = re.compile(r"\{([^{}]*)\}")
_STA_CODE_RE = re.compile(r"[A-Z][0-9a-z]")

Stratum = tuple[str, str, str]
PositionId = tuple[str, int, int]
CellKey = tuple[str, Stratum, tuple[int, int], bool, str]


@dataclass(frozen=True)
class FamilySlot:
    """One certain-boundary component slot, valid or invalid."""

    source: str
    family: str | None
    reasons: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return self.family is not None


@dataclass(frozen=True)
class ZGPosition:
    """One ordinally aligned ZL/GC skeleton position."""

    index: int
    position_id: PositionId
    stratum: Stratum
    paragraph_initial: bool
    line_position: str
    zl_source: str
    gc_source: str
    zl_family: str | None
    gc_family: str | None
    valid: bool
    run_id: str | None


@dataclass(frozen=True)
class ZGTarget:
    """A frozen target and its exact ordered predecessor positions."""

    position: int
    context: tuple[int, ...]
    stratum: Stratum
    run_id: str


@dataclass(frozen=True)
class ZGSkeleton:
    """Frozen ZL/GC skeleton plus complete audit trail."""

    positions: tuple[ZGPosition, ...]
    targets: tuple[ZGTarget, ...]
    cells: tuple[tuple[CellKey, tuple[int, ...]], ...]
    exclusions: tuple[dict[str, Any], ...]
    resets: tuple[dict[str, Any], ...]
    reserved_pages: tuple[str, ...]


def _is_reserved(page_id: str) -> bool:
    return sha256(f"H004-v1:{page_id}".encode("ascii")).digest()[0] < 51


def _line_position(index: int, count: int) -> str:
    if count == 1:
        return "singleton"
    if index == 0:
        return "first"
    if index == count - 1:
        return "last"
    return "middle"


def sta_family_slots(text: str) -> tuple[FamilySlot, ...]:
    """Return ordered STA-family slots while retaining invalid components.

    Only certain boundaries split slots.  An invalid nonempty component remains
    in the ordinal count, exactly as required by H004-C-v1.
    """

    value = text.replace("<->", ".").replace("<~>", ".")
    value = _INLINE_TAG_RE.sub("", value)
    while _LIGATURE_RE.search(value):
        value = _LIGATURE_RE.sub(r"\1", value)
    value = re.sub(r"\s+", "", value)

    slots: list[FamilySlot] = []
    for component in value.split("."):
        if not component:
            continue
        reasons: list[str] = []
        if "," in component:
            reasons.append("uncertain_space")
        if any(marker in component for marker in ("[", "]", ":")):
            reasons.append("alternative_reading")
        if "?" in component:
            reasons.append("unreadable_glyph")
        if "Z1" in component:
            reasons.append("unknown_sta_glyph")
        if "{" in component or "}" in component:
            reasons.append("malformed_ligature")

        codes = _STA_CODE_RE.findall(component)
        if not codes or "".join(codes) != component:
            reasons.append("malformed_sta_or_residue")

        unique_reasons = tuple(dict.fromkeys(reasons))
        family = None if unique_reasons else "".join(code[0] for code in codes)
        slots.append(FamilySlot(component, family, unique_reasons))
    return tuple(slots)


def _single_locus_map(document: Document, page_id: str) -> dict[int, list[Locus]]:
    result: dict[int, list[Locus]] = defaultdict(list)
    for page in document.pages:
        if page.page_id != page_id:
            continue
        for locus in page.loci:
            result[locus.number].append(locus)
    return dict(result)


def _known_stratum(locus: Locus) -> Stratum | None:
    values = tuple(locus.effective_variables.get(name) for name in "ILH")
    if any(value in (None, "", "@", "unknown") for value in values):
        return None
    return values  # type: ignore[return-value]


def _position_id_json(position_id: PositionId) -> list[str | int]:
    return [position_id[0], position_id[1], position_id[2]]


def build_zg_skeleton(zl: Document, gc: Document, *, window: int = WINDOW) -> ZGSkeleton:
    """Build the frozen strict ordinal ZL/GC H004-C skeleton."""

    if zl.header.alphabet != "STA1" or gc.header.alphabet != "STA1":
        raise ValueError("H004-C pre-IT stage requires STA1 ZL and GC documents")
    if window != WINDOW:
        raise ValueError(f"H004-C-v1 freezes window={WINDOW}")

    gc_page_ids = {page.page_id for page in gc.pages}
    reserved_pages = tuple(page.page_id for page in zl.pages if _is_reserved(page.page_id))
    positions: list[ZGPosition] = []
    targets: list[ZGTarget] = []
    exclusions: list[dict[str, Any]] = []
    resets: list[dict[str, Any]] = []
    cells: dict[CellKey, list[int]] = defaultdict(list)

    for page_id in reserved_pages:
        active_run: list[int] = []
        active_run_id: str | None = None
        run_counter = 0
        last_stratum: Stratum | None = None

        def reset(reason: str, *, locus_number: int | None = None, detail: str | None = None) -> None:
            nonlocal active_run_id
            event: dict[str, Any] = {"page_id": page_id, "reason": reason}
            if locus_number is not None:
                event["locus_number"] = locus_number
            if detail is not None:
                event["detail"] = detail
            resets.append(event)
            active_run.clear()
            active_run_id = None

        def ensure_run() -> str:
            nonlocal active_run_id, run_counter
            if active_run_id is None:
                run_counter += 1
                active_run_id = f"{page_id}:run:{run_counter}"
            return active_run_id

        reset("page_boundary")
        if page_id not in gc_page_ids:
            exclusions.append({"page_id": page_id, "reason": "missing_gc_page"})
            reset("hard_gap", detail="missing_gc_page")
            continue

        zl_map = _single_locus_map(zl, page_id)
        gc_map = _single_locus_map(gc, page_id)
        for locus_number in sorted(set(zl_map) | set(gc_map)):
            zl_candidates = zl_map.get(locus_number, [])
            gc_candidates = gc_map.get(locus_number, [])
            zl_has_p = any(item.generic_type == "P" for item in zl_candidates)
            gc_has_p = any(item.generic_type == "P" for item in gc_candidates)
            if not zl_has_p and not gc_has_p:
                continue

            gap_reasons: list[str] = []
            if len(zl_candidates) != 1:
                gap_reasons.append("missing_or_duplicate_zl_locus")
            if len(gc_candidates) != 1:
                gap_reasons.append("missing_or_duplicate_gc_locus")
            if gap_reasons:
                for reason in gap_reasons:
                    exclusions.append(
                        {"page_id": page_id, "locus_number": locus_number, "reason": reason}
                    )
                reset("hard_gap", locus_number=locus_number, detail=";".join(gap_reasons))
                last_stratum = None
                continue

            zl_locus = zl_candidates[0]
            gc_locus = gc_candidates[0]
            if zl_locus.generic_type != "P" or gc_locus.generic_type != "P":
                reason = "generic_type_mismatch_or_nonprose"
                exclusions.append(
                    {"page_id": page_id, "locus_number": locus_number, "reason": reason}
                )
                reset("hard_gap", locus_number=locus_number, detail=reason)
                last_stratum = None
                continue
            if zl_locus.locator == "!" or gc_locus.locator == "!":
                reason = "invalid_locator"
                exclusions.append(
                    {"page_id": page_id, "locus_number": locus_number, "reason": reason}
                )
                reset("hard_gap", locus_number=locus_number, detail=reason)
                last_stratum = None
                continue

            zl_stratum = _known_stratum(zl_locus)
            gc_stratum = _known_stratum(gc_locus)
            if zl_stratum is None or gc_stratum is None:
                reason = "unknown_stratum"
                exclusions.append(
                    {"page_id": page_id, "locus_number": locus_number, "reason": reason}
                )
                reset("hard_gap", locus_number=locus_number, detail=reason)
                last_stratum = None
                continue
            if zl_stratum != gc_stratum:
                reason = "stratum_mismatch"
                exclusions.append(
                    {
                        "page_id": page_id,
                        "locus_number": locus_number,
                        "reason": reason,
                        "zl": list(zl_stratum),
                        "gc": list(gc_stratum),
                    }
                )
                reset("hard_gap", locus_number=locus_number, detail=reason)
                last_stratum = None
                continue
            stratum = zl_stratum

            zl_slots = sta_family_slots(zl_locus.text)
            gc_slots = sta_family_slots(gc_locus.text)
            if len(zl_slots) != len(gc_slots):
                reason = "component_count_mismatch"
                exclusions.append(
                    {
                        "page_id": page_id,
                        "locus_number": locus_number,
                        "reason": reason,
                        "zl_count": len(zl_slots),
                        "gc_count": len(gc_slots),
                    }
                )
                reset("hard_gap", locus_number=locus_number, detail=reason)
                last_stratum = None
                continue

            start_disagreement = zl_locus.paragraph_start != gc_locus.paragraph_start
            end_disagreement = zl_locus.paragraph_end != gc_locus.paragraph_end
            if zl_locus.paragraph_start or gc_locus.paragraph_start:
                reset(
                    "paragraph_boundary_disagreement" if start_disagreement else "paragraph_start",
                    locus_number=locus_number,
                )
            if last_stratum is not None and stratum != last_stratum:
                reset("stratum_change", locus_number=locus_number)
            last_stratum = stratum

            for ordinal, (zl_slot, gc_slot) in enumerate(zip(zl_slots, gc_slots)):
                position_id: PositionId = (page_id, locus_number, ordinal)
                disagreement_reasons: list[str] = []
                if start_disagreement and ordinal == 0:
                    disagreement_reasons.append("paragraph_start_disagreement")
                if end_disagreement and ordinal == len(zl_slots) - 1:
                    disagreement_reasons.append("paragraph_end_disagreement")

                valid = zl_slot.valid and gc_slot.valid and not disagreement_reasons
                for witness, slot in (("ZL", zl_slot), ("GC", gc_slot)):
                    for reason in slot.reasons:
                        exclusions.append(
                            {
                                "page_id": page_id,
                                "locus_number": locus_number,
                                "component_ordinal": ordinal,
                                "witness": witness,
                                "reason": reason,
                            }
                        )
                for reason in disagreement_reasons:
                    exclusions.append(
                        {
                            "page_id": page_id,
                            "locus_number": locus_number,
                            "component_ordinal": ordinal,
                            "witness": "shared",
                            "reason": reason,
                        }
                    )

                run_id = ensure_run() if valid else None
                paragraph_initial = (
                    ordinal == 0
                    and zl_locus.paragraph_start
                    and gc_locus.paragraph_start
                    and not start_disagreement
                )
                position = ZGPosition(
                    index=len(positions),
                    position_id=position_id,
                    stratum=stratum,
                    paragraph_initial=paragraph_initial,
                    line_position=_line_position(ordinal, len(zl_slots)),
                    zl_source=zl_slot.source,
                    gc_source=gc_slot.source,
                    zl_family=zl_slot.family,
                    gc_family=gc_slot.family,
                    valid=valid,
                    run_id=run_id,
                )
                positions.append(position)

                if not valid:
                    reset("invalid_or_disputed_component", locus_number=locus_number)
                    continue

                assert zl_slot.family is not None and gc_slot.family is not None
                cell: CellKey = (
                    page_id,
                    stratum,
                    (len(zl_slot.family), len(gc_slot.family)),
                    paragraph_initial,
                    position.line_position,
                )
                cells[cell].append(position.index)
                active_run.append(position.index)
                if len(active_run) > window:
                    targets.append(
                        ZGTarget(
                            position=position.index,
                            context=tuple(active_run[-window - 1 : -1]),
                            stratum=stratum,
                            run_id=run_id,
                        )
                    )

            if zl_locus.paragraph_end or gc_locus.paragraph_end:
                reset(
                    "paragraph_boundary_disagreement" if end_disagreement else "paragraph_end",
                    locus_number=locus_number,
                )

    return ZGSkeleton(
        positions=tuple(positions),
        targets=tuple(targets),
        cells=tuple((key, tuple(indexes)) for key, indexes in cells.items()),
        exclusions=tuple(exclusions),
        resets=tuple(resets),
        reserved_pages=reserved_pages,
    )


def skeleton_inventory(skeleton: ZGSkeleton) -> dict[str, Any]:
    """Return frozen breadth and audit counts without running permutations."""

    pages = {skeleton.positions[target.position].position_id[0] for target in skeleton.targets}
    currier_targets = Counter(target.stratum[1] for target in skeleton.targets)
    currier_pages = {
        currier: len(
            {
                skeleton.positions[target.position].position_id[0]
                for target in skeleton.targets
                if target.stratum[1] == currier
            }
        )
        for currier in ("A", "B")
    }
    distinct_by_position: dict[int, int] = {}
    for _, indexes in skeleton.cells:
        distinct = len(
            {
                (
                    skeleton.positions[index].zl_family,
                    skeleton.positions[index].gc_family,
                )
                for index in indexes
            }
        )
        for index in indexes:
            distinct_by_position[index] = distinct
    movable = sum(distinct_by_position.get(target.position, 0) > 1 for target in skeleton.targets)
    total = len(skeleton.targets)
    return {
        "reserved_pages_in_zl": len(skeleton.reserved_pages),
        "aligned_positions": len(skeleton.positions),
        "valid_positions": sum(position.valid for position in skeleton.positions),
        "invalid_positions": sum(not position.valid for position in skeleton.positions),
        "pages_with_targets": len(pages),
        "targets": total,
        "currier_pages": currier_pages,
        "currier_targets": {key: currier_targets.get(key, 0) for key in ("A", "B")},
        "movable_targets": movable,
        "movable_target_fraction": movable / total if total else 0.0,
        "exclusion_events": len(skeleton.exclusions),
        "reset_events": len(skeleton.resets),
        "exclusion_reason_counts": dict(
            sorted(Counter(event["reason"] for event in skeleton.exclusions).items())
        ),
        "reset_reason_counts": dict(
            sorted(Counter(event["reason"] for event in skeleton.resets).items())
        ),
    }


def _metric_counts(
    skeleton: ZGSkeleton, tuples_by_position: list[tuple[str | None, str | None]]
) -> tuple[dict[str, dict[str, list[int]]], dict[str, dict[str, list[int]]]]:
    """Compute page and Currier counts in one pass over the frozen events."""

    page_counts: dict[str, dict[str, list[int]]] = {
        "ZL": defaultdict(lambda: [0, 0, 0, 0]),
        "GC": defaultdict(lambda: [0, 0, 0, 0]),
    }
    currier_counts: dict[str, dict[str, list[int]]] = {
        "ZL": defaultdict(lambda: [0, 0, 0, 0]),
        "GC": defaultdict(lambda: [0, 0, 0, 0]),
    }
    for target in skeleton.targets:
        page_id = skeleton.positions[target.position].position_id[0]
        currier = target.stratum[1]
        for witness_index, witness in enumerate(("ZL", "GC")):
            target_family = tuples_by_position[target.position][witness_index]
            assert target_family is not None
            minimum = min(
                edit_distance_class(
                    target_family,
                    tuples_by_position[context_index][witness_index] or "",
                )
                for context_index in target.context
            )
            for row in (page_counts[witness][page_id], currier_counts[witness][currier]):
                row[0] += minimum <= 1
                row[1] += minimum == 1
                row[2] += minimum == 0
                row[3] += 1
    return page_counts, currier_counts


def _page_rates(counts: dict[str, list[int]], page_order: tuple[str, ...]) -> tuple[list[tuple[float, float, float]], tuple[float, float, float]]:
    rows = [
        tuple(counts[page][index] / counts[page][3] for index in range(3))
        for page in page_order
    ]
    overall = tuple(statistics.fmean(row[index] for row in rows) for index in range(3))
    return rows, overall  # type: ignore[return-value]


def _nearest_rank(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    rank = max(1, math.ceil(quantile * len(ordered)))
    return ordered[rank - 1]


def _metric_report(
    observed: float,
    null: list[float],
    page_ids: tuple[str, ...],
    page_observed: list[float],
    page_null_sums: list[float],
) -> dict[str, Any]:
    null_mean = statistics.fmean(null)
    residual_rows = []
    for index, page_id in enumerate(page_ids):
        page_null_mean = page_null_sums[index] / len(null)
        residual = page_observed[index] - page_null_mean
        residual_rows.append(
            {
                "page_id": page_id,
                "observed": round(page_observed[index], 8),
                "null_mean": round(page_null_mean, 8),
                "residual": round(residual, 8),
                "sign": "positive" if residual > 0 else "negative" if residual < 0 else "zero",
            }
        )
    positive = sum(row["sign"] == "positive" for row in residual_rows)
    zero = sum(row["sign"] == "zero" for row in residual_rows)
    negative = len(residual_rows) - positive - zero
    p_value = (1 + sum(value >= observed for value in null)) / (len(null) + 1)
    delta = observed - null_mean
    return {
        "observed_equal_page_mean": round(observed, 8),
        "null_mean": round(null_mean, 8),
        "delta": round(delta, 8),
        "monte_carlo_p": round(p_value, 8),
        "null_quantiles": {
            "q025": round(_nearest_rank(null, 0.025), 8),
            "q05": round(_nearest_rank(null, 0.05), 8),
            "q50": round(_nearest_rank(null, 0.50), 8),
            "q95": round(_nearest_rank(null, 0.95), 8),
            "q975": round(_nearest_rank(null, 0.975), 8),
        },
        "positive_pages": positive,
        "zero_pages": zero,
        "negative_pages": negative,
        "positive_page_fraction": round(positive / len(residual_rows), 8),
        "page_residuals": residual_rows,
        "gate_checks": {
            "delta_at_least_0_02": delta >= 0.02,
            "p_at_most_0_005": p_value <= 0.005,
            "positive_page_fraction_above_0_60": positive / len(residual_rows) > 0.60,
        },
    }


def _shuffle_joint_tuples(
    base: list[tuple[str | None, str | None]],
    cells: tuple[tuple[CellKey, tuple[int, ...]], ...],
    rng: random.Random,
) -> list[tuple[str | None, str | None]]:
    result = list(base)
    for _, indexes in cells:
        if len(indexes) < 2:
            continue
        values = [base[index] for index in indexes]
        rng.shuffle(values)
        for index, value in zip(indexes, values):
            result[index] = value
    return result


def run_zg_discovery(
    skeleton: ZGSkeleton,
    *,
    permutations: int = PERMUTATIONS,
    seed: int = SEED,
) -> dict[str, Any]:
    """Evaluate the frozen joint ZL/GC matched null."""

    if permutations < 1:
        raise ValueError("permutations must be positive")
    if not skeleton.targets:
        raise ValueError("H004-C ZL/GC skeleton contains no targets")

    inventory = skeleton_inventory(skeleton)
    page_order = tuple(
        page_id
        for page_id in skeleton.reserved_pages
        if any(
            skeleton.positions[target.position].position_id[0] == page_id
            for target in skeleton.targets
        )
    )
    base = [(position.zl_family, position.gc_family) for position in skeleton.positions]
    observed_page_counts, observed_currier_counts = _metric_counts(skeleton, base)
    observed_rows: dict[str, list[tuple[float, float, float]]] = {}
    observed_overall: dict[str, tuple[float, float, float]] = {}
    for witness in ("ZL", "GC"):
        rows, overall = _page_rates(observed_page_counts[witness], page_order)
        observed_rows[witness] = rows
        observed_overall[witness] = overall

    null: dict[str, list[list[float]]] = {
        witness: [[], [], []] for witness in ("ZL", "GC")
    }
    page_null_sums: dict[str, list[list[float]]] = {
        witness: [[0.0, 0.0, 0.0] for _ in page_order] for witness in ("ZL", "GC")
    }
    currier_null: dict[str, dict[str, list[list[float]]]] = {
        witness: {currier: [[], [], []] for currier in ("A", "B")}
        for witness in ("ZL", "GC")
    }

    rng = random.Random(seed)
    for _ in range(permutations):
        shuffled = _shuffle_joint_tuples(base, skeleton.cells, rng)
        page_counts, currier_counts = _metric_counts(skeleton, shuffled)
        for witness in ("ZL", "GC"):
            rows, overall = _page_rates(page_counts[witness], page_order)
            for metric in range(3):
                null[witness][metric].append(overall[metric])
                for page_index, row in enumerate(rows):
                    page_null_sums[witness][page_index][metric] += row[metric]
            for currier in ("A", "B"):
                values = currier_counts[witness].get(currier, [0, 0, 0, 0])
                for metric in range(3):
                    rate = values[metric] / values[3] if values[3] else 0.0
                    currier_null[witness][currier][metric].append(rate)

    names = ("C_exact_or_one_edit", "U_one_edit_without_exact", "E_exact_repeat")
    witness_results: dict[str, Any] = {}
    for witness in ("ZL", "GC"):
        metrics = {
            name: _metric_report(
                observed_overall[witness][metric],
                null[witness][metric],
                page_order,
                [row[metric] for row in observed_rows[witness]],
                [row[metric] for row in page_null_sums[witness]],
            )
            for metric, name in enumerate(names)
        }
        currier_results: dict[str, Any] = {}
        for currier in ("A", "B"):
            observed_counts = observed_currier_counts[witness].get(currier, [0, 0, 0, 0])
            result_metrics: dict[str, Any] = {}
            for metric, name in enumerate(names[:2]):
                observed = observed_counts[metric] / observed_counts[3] if observed_counts[3] else 0.0
                distribution = currier_null[witness][currier][metric]
                null_mean = statistics.fmean(distribution)
                p_value = (1 + sum(value >= observed for value in distribution)) / (
                    permutations + 1
                )
                delta = observed - null_mean
                result_metrics[name] = {
                    "observed": round(observed, 8),
                    "null_mean": round(null_mean, 8),
                    "delta": round(delta, 8),
                    "monte_carlo_p": round(p_value, 8),
                    "gate_checks": {
                        "delta_positive": delta > 0,
                        "p_at_most_0_025": p_value <= 0.025,
                    },
                }
            currier_results[currier] = {
                "pages": inventory["currier_pages"][currier],
                "targets": observed_counts[3],
                "metrics": result_metrics,
            }
        witness_results[witness] = {"metrics": metrics, "currier": currier_results}

    breadth_checks = {
        "at_least_30_reserved_pages": inventory["pages_with_targets"] >= 30,
        "at_least_1500_targets": inventory["targets"] >= 1500,
        "currier_A_at_least_5_pages_and_200_targets": inventory["currier_pages"]["A"] >= 5
        and inventory["currier_targets"]["A"] >= 200,
        "currier_B_at_least_5_pages_and_200_targets": inventory["currier_pages"]["B"] >= 5
        and inventory["currier_targets"]["B"] >= 200,
        "movable_target_fraction_at_least_0_80": inventory["movable_target_fraction"] >= 0.80,
    }
    primary_checks = [
        check
        for witness in ("ZL", "GC")
        for name in names[:2]
        for check in witness_results[witness]["metrics"][name]["gate_checks"].values()
    ]
    currier_checks = [
        check
        for witness in ("ZL", "GC")
        for currier in ("A", "B")
        for name in names[:2]
        for check in witness_results[witness]["currier"][currier]["metrics"][name][
            "gate_checks"
        ].values()
    ]
    breadth_gate_met = all(breadth_checks.values())
    primary_effect_gate_met = all(primary_checks)
    currier_effect_gate_met = all(currier_checks)
    effect_gate_met = primary_effect_gate_met and currier_effect_gate_met
    gate_met = breadth_gate_met and effect_gate_met
    return {
        "permutations": permutations,
        "permutations_requested": permutations,
        "permutations_run": permutations,
        "seed_label": SEED_LABEL,
        "seed_unsigned_big_endian_128": seed,
        "seed_initialized": True,
        "metrics": {
            "C": "minimum STA-family Levenshtein distance to exact preceding ten IDs is <=1",
            "U": "minimum distance is exactly 1; an exact predecessor excludes the target",
            "E": "minimum distance is 0; diagnostic only",
        },
        "inventory": inventory,
        "breadth_checks": breadth_checks,
        "breadth_gate_met": breadth_gate_met,
        "primary_effect_gate_met": primary_effect_gate_met,
        "currier_effect_gate_met": currier_effect_gate_met,
        "effect_gate_met": effect_gate_met,
        "witness_effect_results_evaluated": True,
        "witness_results": witness_results,
        "pre_it_zg_gate_met": gate_met,
        "it_event_projection_authorized": gate_met,
        "disposition": (
            "ZL/GC STA-family gate passed; frozen IT projection may proceed in a separate task"
            if gate_met
            else "reject H004 as a ZL/GC-robust STA-family route; leave IT event projection unrun"
        ),
    }


def _position_manifest(position: ZGPosition, cell_distinct: int | None) -> dict[str, Any]:
    return {
        "index": position.index,
        "position_id": _position_id_json(position.position_id),
        "stratum_I_L_H": list(position.stratum),
        "paragraph_initial": position.paragraph_initial,
        "line_position": position.line_position,
        "zl_source": position.zl_source,
        "gc_source": position.gc_source,
        "zl_family": position.zl_family,
        "gc_family": position.gc_family,
        "family_length_vector": (
            [len(position.zl_family), len(position.gc_family)]
            if position.valid and position.zl_family is not None and position.gc_family is not None
            else None
        ),
        "valid": position.valid,
        "run_id": position.run_id,
        "cell_distinct_tuple_count": cell_distinct,
    }


def build_discovery_manifest(
    zl: Document,
    gc: Document,
    *,
    protocol_text: str,
    protocol_path: str,
    permutations: int = PERMUTATIONS,
) -> dict[str, Any]:
    """Build the complete frozen machine-readable pre-IT manifest."""

    zl_hash = sha256(zl.source).hexdigest()
    gc_hash = sha256(gc.source).hexdigest()
    if zl_hash != ZL_SHA256:
        raise ValueError(f"unexpected ZL STA1 SHA-256: {zl_hash}")
    if gc_hash != GC_SHA256:
        raise ValueError(f"unexpected GC STA1 SHA-256: {gc_hash}")

    skeleton = build_zg_skeleton(zl, gc)
    analysis = run_zg_discovery(skeleton, permutations=permutations)

    distinct_by_position: dict[int, int] = {}
    cell_rows = []
    for key, indexes in skeleton.cells:
        distinct = len(
            {
                (skeleton.positions[index].zl_family, skeleton.positions[index].gc_family)
                for index in indexes
            }
        )
        for index in indexes:
            distinct_by_position[index] = distinct
        cell_rows.append(
            {
                "page_id": key[0],
                "stratum_I_L_H": list(key[1]),
                "family_length_vector": list(key[2]),
                "paragraph_initial": key[3],
                "line_position": key[4],
                "position_indexes": list(indexes),
                "distinct_tuple_count": distinct,
            }
        )

    position_rows = [
        _position_manifest(position, distinct_by_position.get(position.index))
        for position in skeleton.positions
    ]
    target_rows = [
        {
            "target_index": target.position,
            "target_id": _position_id_json(skeleton.positions[target.position].position_id),
            "context_indexes": list(target.context),
            "context_ids": [
                _position_id_json(skeleton.positions[index].position_id) for index in target.context
            ],
            "stratum_I_L_H": list(target.stratum),
            "run_id": target.run_id,
            "movable": distinct_by_position.get(target.position, 0) > 1,
        }
        for target in skeleton.targets
    ]

    target_invariants = {
        "all_contexts_have_exactly_10_positions": all(
            len(target.context) == WINDOW for target in skeleton.targets
        ),
        "all_target_and_context_positions_are_valid": all(
            skeleton.positions[target.position].valid
            and all(skeleton.positions[index].valid for index in target.context)
            for target in skeleton.targets
        ),
        "all_contexts_share_target_run": all(
            all(
                skeleton.positions[index].run_id == target.run_id for index in target.context
            )
            and skeleton.positions[target.position].run_id == target.run_id
            for target in skeleton.targets
        ),
        "all_context_indexes_precede_targets": all(
            all(index < target.position for index in target.context) for target in skeleton.targets
        ),
    }
    if not all(target_invariants.values()):
        raise AssertionError(f"H004-C target invariant failed: {target_invariants}")

    return {
        "hypothesis_id": "H004-C",
        "analysis_version": ANALYSIS_VERSION,
        "stage": STAGE,
        "claim_scope": "cross-transcription STA-family local-order discovery; no IT outcome, semantics, or generator claim",
        "protocol": {
            "path": protocol_path,
            "sha256": sha256(protocol_text.encode("utf-8")).hexdigest(),
            "text": protocol_text,
        },
        "execution_audit": {
            "breadth_gate_evaluated": True,
            "breadth_gate_met": analysis["breadth_gate_met"],
            "zg_permutations_completed": analysis["permutations_run"],
            "effect_gate_met": analysis["effect_gate_met"],
            "zg_permutations_completed_after_breadth_failure": (
                not analysis["breadth_gate_met"]
                and analysis["permutations_run"] > 0
            ),
            "chronology": (
                "The strict ZL/GC skeleton failed the frozen breadth gate. The implementation "
                "nevertheless completed and exposed the ZL/GC permutation results before a "
                "short-circuit correction was requested. Those already-inspected results are "
                "retained as audit evidence; they also fail the effect gates and cannot "
                "authorize IT event projection."
            ),
            "it_event_projection_run": False,
        },
        "inputs": {
            "zl_sta1": {"sha256": zl_hash, "alphabet": zl.header.alphabet},
            "gc_sta1_level0": {"sha256": gc_hash, "alphabet": gc.header.alphabet},
            "reserved_it_sta1": {
                "declared_sha256": DECLARED_RESERVED_IT_SHA256,
                "opened_by_this_analysis": False,
                "parsed_by_this_analysis": False,
                "projected_by_this_analysis": False,
                "prior_project_integrity_and_header_inspection": True,
                "prior_h004_event_projection": False,
            },
        },
        "specifications": {
            "ivtff_observed_sha256": IVTFF_SPEC_SHA256,
            "sta1_observed_sha256": STA1_SPEC_SHA256,
        },
        "frozen_rules": {
            "reserved_page_rule": "SHA256('H004-v1:' + page_id)[0] < 51",
            "window": WINDOW,
            "position_id": ["page_id", "locus_number", "component_ordinal"],
            "alignment": "exact locus key, equal slot count, ordinal only; no similarity alignment",
            "distance": "unit-cost Levenshtein over repeated, ordered STA family letters; cap at 0, 1, >1",
            "null_cell": [
                "page",
                "I",
                "L",
                "H",
                "ZL_GC_family_length_vector",
                "paragraph_initial",
                "line_position",
            ],
            "shuffle_object": "joint (ZL_family, GC_family) tuple",
            "aggregation": "within-page rates, then equal mean across pages",
        },
        "skeleton": {
            "positions": position_rows,
            "cells": cell_rows,
            "targets": target_rows,
            "exclusions": list(skeleton.exclusions),
            "resets": list(skeleton.resets),
            "target_invariants": target_invariants,
        },
        "zg_discovery": analysis,
    }


def canonical_manifest_bytes(manifest: dict[str, Any]) -> bytes:
    """Return deterministic bytes whose SHA-256 is recorded beside the manifest."""

    return (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")


def render_zg_discovery_markdown(manifest: dict[str, Any], manifest_sha256: str) -> str:
    """Render a compact human-readable pre-IT discovery report."""

    result = manifest["zg_discovery"]
    inventory = result["inventory"]
    lines = [
        "# H004-C pre-IT ZL/GC discovery",
        "",
        (
            "> STA-family structural analysis only. This analysis did not load IT bytes or "
            "project IT event data; the pinned IT file had prior integrity/header inspection "
            "before protocol freeze."
        ),
        "",
        f"- Protocol: `{manifest['analysis_version']}`",
        f"- Protocol SHA-256: `{manifest['protocol']['sha256']}`",
        f"- Manifest SHA-256: `{manifest_sha256}`",
        (
            f"- Joint permutations run / requested: {result['permutations_run']} / "
            f"{result['permutations_requested']}"
        ),
        f"- Reserved pages with targets / targets: {inventory['pages_with_targets']} / {inventory['targets']}",
        f"- Valid / invalid aligned positions: {inventory['valid_positions']} / {inventory['invalid_positions']}",
        f"- Movable targets: {inventory['movable_targets']} ({inventory['movable_target_fraction']:.2%})",
        f"- Currier A pages / targets: {inventory['currier_pages']['A']} / {inventory['currier_targets']['A']}",
        f"- Currier B pages / targets: {inventory['currier_pages']['B']} / {inventory['currier_targets']['B']}",
        f"- Pre-IT ZL/GC gate: `{'met' if result['pre_it_zg_gate_met'] else 'not met'}`",
        "",
        "## Execution chronology",
        "",
        manifest["execution_audit"]["chronology"],
    ]
    labels = {
        "C_exact_or_one_edit": "C: exact or one edit",
        "U_one_edit_without_exact": "U: one edit, no exact",
        "E_exact_repeat": "E: exact repeat (diagnostic)",
    }
    if result["witness_effect_results_evaluated"]:
        lines.extend(
            [
                "",
                "| Witness | Metric | Observed | Null mean | Delta | Monte Carlo p | Positive pages |",
                "|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for witness in ("ZL", "GC"):
            for name, label in labels.items():
                metric = result["witness_results"][witness]["metrics"][name]
                lines.append(
                    f"| {witness} | {label} | {metric['observed_equal_page_mean']:.6f} | "
                    f"{metric['null_mean']:.6f} | {metric['delta']:+.6f} | "
                    f"{metric['monte_carlo_p']:.6f} | {metric['positive_pages']} |"
                )
        lines.extend(
            [
            "",
            "## Currier checks",
            "",
            "| Witness | Currier | Metric | Targets | Delta | Monte Carlo p | Gate |",
            "|---|---|---|---:|---:|---:|:---:|",
            ]
        )
        for witness in ("ZL", "GC"):
            for currier in ("A", "B"):
                row = result["witness_results"][witness]["currier"][currier]
                for name in ("C_exact_or_one_edit", "U_one_edit_without_exact"):
                    metric = row["metrics"][name]
                    gate = all(metric["gate_checks"].values())
                    lines.append(
                        f"| {witness} | {currier} | {name[0]} | {row['targets']} | "
                        f"{metric['delta']:+.6f} | {metric['monte_carlo_p']:.6f} | "
                        f"{'yes' if gate else 'no'} |"
                    )
    else:
        lines.extend(
            [
                "",
                "## Witness effect results",
                "",
                f"Not evaluated: {result['not_evaluated_reason']}.",
            ]
        )
    lines.extend(
        [
            "",
            f"Disposition: {result['disposition']}.",
            "",
            (
                "The JSON manifest records every aligned position, frozen target/context ID, "
                "exclusion, reset, cell, and input/specification hash. No witness effect "
                "estimate, null tail, or page residual was computed after the breadth failure."
                if not result["witness_effect_results_evaluated"]
                else "The JSON manifest records every aligned position, frozen target/context ID, exclusion, reset, cell, input/specification hash, and page residual. Witness tuples were shuffled jointly; witness p-values were not pooled."
            ),
            "",
        ]
    )
    return "\n".join(lines)
