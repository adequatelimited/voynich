"""P001: reproducible scratch pilot for atomic edge-slot morphology.

This module is intentionally isolated from the hypothesis pipeline.  P001 was
designed and evaluated in one scratch session, so its partition names are data
partitions, not evidence of a preregistered or untouched confirmation test.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from fractions import Fraction
from itertools import combinations
import re
from typing import Any, Iterable, Literal

from .ivtff import Document


PILOT_ID = "P001"
SPLIT_TAG = "H004-v1"
TRAIN_MAX = 154
CALIBRATION_MAX = 205
MIN_EDGE_RESIDUAL_TYPES = 10
MIN_EDGE_TOKENS = 50
MIN_EDGE_EXCLUSIVITY = 0.80
CONTROL_PERCENTILE_GATE = 0.95

_INLINE_COMMENT_RE = re.compile(r"<[^>]*>")
_LIGATURE_RE = re.compile(r"\{([^{}]*)\}")
_STA_CODE_RE = re.compile(r"[A-Z][0-9a-z]")


def partition_for_page(page_id: str) -> Literal["train", "calibration", "test"]:
    """Return the exact page partition used in the simultaneous scratch pilot."""

    first_byte = sha256(f"{SPLIT_TAG}:{page_id}".encode("ascii")).digest()[0]
    if first_byte < TRAIN_MAX:
        return "train"
    if first_byte < CALIBRATION_MAX:
        return "calibration"
    return "test"


def strict_sta1_family_words(text: str) -> tuple[str, ...]:
    """Extract certain-space STA1 words and reduce codes to STA families.

    Drawing boundaries count as certain word boundaries.  Components containing
    uncertain spaces, alternatives, unreadable glyphs, or malformed STA1 are
    excluded rather than repaired or assigned a preferred reading.
    """

    value = text.replace("<->", ".").replace("<~>", ".")
    value = _INLINE_COMMENT_RE.sub("", value)
    while _LIGATURE_RE.search(value):
        value = _LIGATURE_RE.sub(r"\1", value)
    value = re.sub(r"\s+", "", value)

    words: list[str] = []
    for component in value.split("."):
        if not component:
            continue
        if any(marker in component for marker in (",", "[", "]", "?", "Z1")):
            continue
        codes = _STA_CODE_RE.findall(component)
        if not codes or "".join(codes) != component:
            continue
        words.append("".join(code[0] for code in codes))
    return tuple(words)


def split_family_word(
    word: str,
    prefix_families: Iterable[str],
    suffix_families: Iterable[str],
) -> tuple[str, str, str]:
    """Apply the pilot's optional one-family prefix/core/suffix parse.

    Prefix stripping has priority.  A suffix is stripped only when at least one
    core family remains, which reproduces the scratch calculation for two-glyph
    words exactly.
    """

    if not word:
        raise ValueError("cannot segment an empty family word")
    prefixes = frozenset(prefix_families)
    suffixes = frozenset(suffix_families)

    prefix = word[0] if len(word) > 1 and word[0] in prefixes else ""
    core_start = 1 if prefix else 0
    suffix = (
        word[-1]
        if len(word) - core_start > 1 and word[-1] in suffixes
        else ""
    )
    core_end = len(word) - 1 if suffix else len(word)
    return prefix, word[core_start:core_end], suffix


def _candidate_inventory(
    train_counts: Counter[str], side: Literal["prefix", "suffix"]
) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    """Select qualifying atomic edge families from training data only."""

    train_types = set(train_counts)
    alphabet = sorted(set("".join(train_types)))
    rows: list[dict[str, Any]] = []
    selected: list[str] = []
    for family in alphabet:
        if side == "prefix":
            edge_types = {
                word for word in train_types if len(word) > 1 and word[0] == family
            }
            residuals = {word[1:] for word in edge_types}
        else:
            edge_types = {
                word for word in train_types if len(word) > 1 and word[-1] == family
            }
            residuals = {word[:-1] for word in edge_types}
        containing_types = {word for word in train_types if family in word}
        edge_tokens = sum(train_counts[word] for word in edge_types)
        exclusivity = (
            len(edge_types) / len(containing_types) if containing_types else 0.0
        )
        qualified = (
            len(residuals) >= MIN_EDGE_RESIDUAL_TYPES
            and edge_tokens >= MIN_EDGE_TOKENS
            and exclusivity >= MIN_EDGE_EXCLUSIVITY
        )
        if qualified:
            selected.append(family)
        rows.append(
            {
                "family": family,
                "edge_residual_types": len(residuals),
                "edge_tokens": edge_tokens,
                "containing_types": len(containing_types),
                "edge_exclusivity": round(exclusivity, 6),
                "qualified": qualified,
            }
        )
    return rows, tuple(selected)


def _evaluate_inventory(
    train_counts: Counter[str],
    evaluation_counts: Counter[str],
    prefix_families: Iterable[str],
    suffix_families: Iterable[str],
) -> dict[str, Any]:
    prefixes = tuple(prefix_families)
    suffixes = tuple(suffix_families)
    train_types = set(train_counts)
    train_tuples = {
        split_family_word(word, prefixes, suffixes) for word in train_types
    }
    train_cores = {parts[1] for parts in train_tuples}
    unseen_types = set(evaluation_counts) - train_types

    affixed_types: list[str] = []
    productive_types: list[str] = []
    for word in unseen_types:
        parts = split_family_word(word, prefixes, suffixes)
        if not (parts[0] or parts[2]):
            continue
        affixed_types.append(word)
        if parts[1] in train_cores and parts not in train_tuples:
            productive_types.append(word)

    affixed_tokens = sum(evaluation_counts[word] for word in affixed_types)
    productive_tokens = sum(evaluation_counts[word] for word in productive_types)
    return {
        "unseen_surface_types": len(unseen_types),
        "unseen_affixed_types": len(affixed_types),
        "productive_unseen_types": len(productive_types),
        "productive_type_rate_among_affixed": round(
            len(productive_types) / len(affixed_types) if affixed_types else 0.0,
            6,
        ),
        "productive_type_coverage_all_unseen": round(
            len(productive_types) / len(unseen_types) if unseen_types else 0.0,
            6,
        ),
        "unseen_affixed_tokens": affixed_tokens,
        "productive_unseen_tokens": productive_tokens,
        "productive_token_rate_among_affixed": round(
            productive_tokens / affixed_tokens if affixed_tokens else 0.0,
            6,
        ),
    }


def _page_support(
    train_counts: Counter[str],
    page_counts: dict[str, Counter[str]],
    prefix_families: tuple[str, ...],
    suffix_families: tuple[str, ...],
) -> dict[str, int]:
    evaluated = 0
    positive = 0
    affixed_total = 0
    productive_total = 0
    for counts in page_counts.values():
        result = _evaluate_inventory(
            train_counts, counts, prefix_families, suffix_families
        )
        if result["unseen_affixed_types"] == 0:
            continue
        evaluated += 1
        affixed_total += result["unseen_affixed_types"]
        productive_total += result["productive_unseen_types"]
        positive += result["productive_unseen_types"] > 0
    return {
        "evaluable_pages": evaluated,
        "pages_with_at_least_one_productive_type": positive,
        "page_counted_unseen_affixed_types": affixed_total,
        "page_counted_productive_types": productive_total,
    }


def _control_ranking(
    train_counts: Counter[str],
    test_counts: Counter[str],
    selected_prefixes: tuple[str, ...],
    selected_suffixes: tuple[str, ...],
) -> dict[str, Any]:
    if len(selected_prefixes) != 1 or len(selected_suffixes) != 2:
        raise ValueError(
            "P001 control requires exactly one selected prefix and two suffix families; "
            f"got {selected_prefixes!r} and {selected_suffixes!r}"
        )

    alphabet = sorted(set("".join(train_counts)))
    target = _evaluate_inventory(
        train_counts, test_counts, selected_prefixes, selected_suffixes
    )
    target_rate = Fraction(
        target["productive_unseen_types"], target["unseen_affixed_types"] or 1
    )

    inventories = 0
    strictly_better = 0
    tied = 0
    for prefix in alphabet:
        for suffix_pair in combinations(alphabet, 2):
            result = _evaluate_inventory(
                train_counts, test_counts, (prefix,), suffix_pair
            )
            rate = Fraction(
                result["productive_unseen_types"],
                result["unseen_affixed_types"] or 1,
            )
            inventories += 1
            if rate > target_rate:
                strictly_better += 1
            elif rate == target_rate:
                tied += 1

    rank = strictly_better + 1
    percentile = 1.0 - strictly_better / inventories
    return {
        "control_definition": (
            "exhaustive one-prefix-family and unordered two-suffix-family "
            "inventories over the training alphabet; the selected inventory is included"
        ),
        "training_alphabet_families": len(alphabet),
        "equal_cardinality_inventories": inventories,
        "alternative_inventories": inventories - 1,
        "inventories_with_strictly_higher_test_rate": strictly_better,
        "inventories_tied_on_test_rate": tied,
        "selected_inventory_rank_from_best": rank,
        "selected_inventory_percentile": round(percentile, 6),
        "advancement_percentile_gate": CONTROL_PERCENTILE_GATE,
        "gate_met": percentile >= CONTROL_PERCENTILE_GATE,
    }


def analyze_edge_morphology(document: Document) -> dict[str, Any]:
    """Reproduce the complete P001 scratch pilot on a pinned STA1 document."""

    if document.header.alphabet != "STA1":
        raise ValueError(
            f"P001 requires an STA1 document; got {document.header.alphabet!r}"
        )

    partition_pages: dict[str, set[str]] = {
        "train": set(),
        "calibration": set(),
        "test": set(),
    }
    partition_counts: dict[str, Counter[str]] = {
        "train": Counter(),
        "calibration": Counter(),
        "test": Counter(),
    }
    page_counts: dict[str, dict[str, Counter[str]]] = {
        "train": {},
        "calibration": {},
        "test": {},
    }

    for locus in document.loci:
        if locus.locator == "!" or locus.generic_type != "P":
            continue
        words = strict_sta1_family_words(locus.text)
        if not words:
            continue
        partition = partition_for_page(locus.page_id)
        partition_pages[partition].add(locus.page_id)
        partition_counts[partition].update(words)
        page_counts[partition].setdefault(locus.page_id, Counter()).update(words)

    train_counts = partition_counts["train"]
    prefix_scan, selected_prefixes = _candidate_inventory(train_counts, "prefix")
    suffix_scan, selected_suffixes = _candidate_inventory(train_counts, "suffix")
    if selected_prefixes != ("D",) or selected_suffixes != ("G", "H"):
        raise ValueError(
            "pinned P001 inventory drifted: expected prefix D and suffixes G/H, "
            f"got {selected_prefixes!r} and {selected_suffixes!r}"
        )

    evaluations: dict[str, Any] = {}
    for name in ("calibration", "test"):
        result = _evaluate_inventory(
            train_counts,
            partition_counts[name],
            selected_prefixes,
            selected_suffixes,
        )
        result["page_support"] = _page_support(
            train_counts, page_counts[name], selected_prefixes, selected_suffixes
        )
        evaluations[name] = result

    control = _control_ranking(
        train_counts,
        partition_counts["test"],
        selected_prefixes,
        selected_suffixes,
    )
    partition_summary = {
        name: {
            "pages_with_accepted_prose_words": len(partition_pages[name]),
            "accepted_tokens": sum(partition_counts[name].values()),
            "family_types": len(partition_counts[name]),
        }
        for name in ("train", "calibration", "test")
    }

    return {
        "pilot_id": PILOT_ID,
        "title": "atomic edge-slot morphology discriminating-control pilot",
        "protocol_status": (
            "Rules and evaluation were developed in one simultaneous scratch session; "
            "this is not a preregistered or confirmatory test"
        ),
        "claim_scope": (
            "whether train-selected atomic edge families form a distinctive productive "
            "prefix/core/suffix mechanism; no semantic, phonetic, or gloss claim"
        ),
        "input": {
            "alphabet": document.header.alphabet,
            "source_sha256": sha256(document.source).hexdigest(),
            "accepted_loci": "substantive P* loci only",
            "word_policy": (
                "certain-space STA1 components only; reject uncertain spaces, alternatives, "
                "unreadable Z1, unknowns, and malformed components"
            ),
            "analytical_unit": (
                "one two-character STA1 code, which may represent a composite; family sequence "
                "retains each code's first character"
            ),
        },
        "split": {
            "tag": SPLIT_TAG,
            "rule": (
                "SHA256('H004-v1:' + page_id): first byte <154 train, "
                "154-204 calibration, >=205 test"
            ),
            "disclosure": (
                "The exact H004-v1 tag is retained for auditability; calibration and test "
                "were inspected during the same scratch session and are not untouched holdouts"
            ),
        },
        "partitions": partition_summary,
        "selection": {
            "candidate_unit": "one STA family at the prefix or suffix edge",
            "minimum_edge_residual_types": MIN_EDGE_RESIDUAL_TYPES,
            "minimum_edge_tokens": MIN_EDGE_TOKENS,
            "minimum_edge_exclusivity": MIN_EDGE_EXCLUSIVITY,
            "edge_exclusivity_definition": (
                "training types placing the family at that edge divided by training types "
                "containing the family anywhere"
            ),
            "prefix_scan": prefix_scan,
            "suffix_scan": suffix_scan,
            "selected_prefix_families": list(selected_prefixes),
            "selected_suffix_families": list(selected_suffixes),
            "segmentation_rule": (
                "optional one-family prefix, nonempty core, optional one-family suffix; "
                "prefix stripping has priority on two-family words"
            ),
        },
        "productive_recombination_definition": (
            "evaluation surface type absent from training, carrying a selected edge family, "
            "whose parsed core occurred in the training core inventory while its complete "
            "slot tuple did not"
        ),
        "evaluation": evaluations,
        "equal_cardinality_control": control,
        "advancement": {
            "criterion": (
                "selected test productive-type rate must reach at least the 95th percentile "
                "of exhaustive equal-cardinality inventories"
            ),
            "criterion_met": control["gate_met"],
            "disposition": (
                "failed discriminating control; do not advance the edge slots as morphology; "
                "assign no gloss"
            ),
        },
    }
