"""Frozen H005-v1 pharmaceutical-fragment referential-anchor screen.

This module evaluates only the ZL/GC stage.  It deliberately has no IT input
or projection path; the frozen protocol reserves IT until the ZL/GC gate has
passed.
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
from typing import Any, Iterable, Mapping, Sequence

from .h004c import sta_family_slots
from .ivtff import Document, Locus, Page


ANALYSIS_VERSION = "H005-v1"
MODEL_IDS = ("M0", "M1")
BM25_K1 = 1.2
BM25_B = 0.75
PERMUTATIONS = 9_999
SEED_LABEL = "H005-v1|target-null|seed=5005"
SEED = int.from_bytes(sha256(SEED_LABEL.encode("ascii")).digest()[:16], "big")

EVA_SHA256 = "bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc"
ZL_STA_SHA256 = "8438ba1c45f47fe1d06b5262cbcdf60ce69158a0edbd4dd802612896f3217e2a"
GC_STA_SHA256 = "b39cabbd9c8c8a098bfa9f76e0649291d17d77e1cb4fb0a3351ff7bdc832ace3"
RESERVED_IT_STA_SHA256 = (
    "215f2d05690828c00bd4ae00d6201df31050adcd81601343b142ae91b9dfeee4"
)
SOURCE_MANIFEST_SHA256 = (
    "f6f6f8edd9b21f5aa1e952e26a6104ad327a15a98e426a1fc4ed8e735b9631c7"
)

_PHYSICAL_FOLIO_RE = re.compile(r"^(f\d+)[rv]\d*$")


@dataclass(frozen=True)
class StrictQuery:
    pair_id: str
    quire: str
    fragment_page: str
    fragment_number: int
    target_page: str
    target_physical_folio: str
    strength: str
    label_loci: tuple[str, ...]
    query_families: tuple[str, ...]
    target_stratum: tuple[str, str]
    split: str
    candidate_pages: tuple[str, ...]


@dataclass(frozen=True)
class QueryAudit:
    pair_id: str
    admitted: bool
    reasons: tuple[str, ...]
    query_families: tuple[str, ...]
    target_physical_folio: str
    split: str


@dataclass(frozen=True)
class ModelRanks:
    model_id: str
    zl_scores: Mapping[str, float]
    gc_scores: Mapping[str, float]
    zl_ranks: Mapping[str, float]
    gc_ranks: Mapping[str, float]

    def conservative_rank(self, page_id: str) -> float:
        return max(self.zl_ranks[page_id], self.gc_ranks[page_id])


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def physical_folio(page_id: str) -> str:
    match = _PHYSICAL_FOLIO_RE.fullmatch(page_id)
    if match is None:
        raise ValueError(f"cannot derive physical folio from {page_id!r}")
    return match.group(1)


def is_holdout_physical_folio(folio_id: str) -> bool:
    return sha256(f"{ANALYSIS_VERSION}:{folio_id}".encode("ascii")).digest()[0] < 51


def family_ngrams(token: str) -> tuple[str, ...]:
    padded = f"^{token}$"
    return tuple(
        padded[index : index + size]
        for size in (2, 3)
        for index in range(len(padded) - size + 1)
    )


def model_features(tokens: Sequence[str], model_id: str) -> tuple[str, ...]:
    if model_id == "M0":
        return tuple(tokens)
    if model_id == "M1":
        return tuple(feature for token in tokens for feature in family_ngrams(token))
    raise ValueError(f"unknown H005 model {model_id!r}")


def bm25_scores(
    query_features: Sequence[str],
    documents: Mapping[str, Sequence[str]],
    *,
    k1: float = BM25_K1,
    b: float = BM25_B,
) -> dict[str, float]:
    """Return fixed-parameter BM25 scores for all documents."""

    if not documents:
        raise ValueError("BM25 requires at least one document")
    if not query_features:
        raise ValueError("BM25 requires at least one query feature")

    counters = {page: Counter(features) for page, features in documents.items()}
    lengths = {page: sum(counter.values()) for page, counter in counters.items()}
    average_length = statistics.fmean(lengths.values())
    if average_length <= 0:
        raise ValueError("BM25 documents must not all be empty")

    document_frequency: Counter[str] = Counter()
    for counter in counters.values():
        document_frequency.update(counter.keys())

    query_counts = Counter(query_features)
    total_documents = len(documents)
    result: dict[str, float] = {}
    for page_id, counter in counters.items():
        score = 0.0
        length_normalizer = 1.0 - b + b * lengths[page_id] / average_length
        for feature, query_frequency in query_counts.items():
            term_frequency = counter.get(feature, 0)
            if term_frequency == 0:
                continue
            df = document_frequency[feature]
            inverse_document_frequency = math.log(
                1.0 + (total_documents - df + 0.5) / (df + 0.5)
            )
            saturation = term_frequency * (k1 + 1.0) / (
                term_frequency + k1 * length_normalizer
            )
            score += query_frequency * inverse_document_frequency * saturation
        result[page_id] = score
    return result


def descending_midranks(scores: Mapping[str, float]) -> dict[str, float]:
    """Rank high scores first, assigning exact-score ties their midrank."""

    result: dict[str, float] = {}
    values = list(scores.values())
    for page_id, value in scores.items():
        greater = sum(other > value for other in values)
        tied = sum(other == value for other in values)
        result[page_id] = 1.0 + greater + (tied - 1) / 2.0
    return result


def _locus_map(document: Document) -> dict[str, list[Locus]]:
    result: dict[str, list[Locus]] = defaultdict(list)
    for locus in document.loci:
        result[f"{locus.page_id}.{locus.number}"].append(locus)
    return dict(result)


def _page_map(document: Document) -> dict[str, list[Page]]:
    result: dict[str, list[Page]] = defaultdict(list)
    for page in document.pages:
        result[page.page_id].append(page)
    return dict(result)


def _single_page(pages: Mapping[str, list[Page]], page_id: str) -> Page | None:
    candidates = pages.get(page_id, [])
    return candidates[0] if len(candidates) == 1 else None


def _valid_family_tokens(loci: Iterable[Locus], *, generic_type: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for locus in loci:
        if locus.locator == "!" or locus.generic_type != generic_type:
            continue
        for slot in sta_family_slots(locus.text):
            if slot.valid:
                assert slot.family is not None
                tokens.append(slot.family)
    return tuple(tokens)


def _page_prose_tokens(page: Page) -> tuple[str, ...]:
    return _valid_family_tokens(page.loci, generic_type="P")


def _known_target_stratum(zl_page: Page, gc_page: Page) -> tuple[str, str] | None:
    zl = tuple(zl_page.variables.get(name) for name in ("L", "H"))
    gc = tuple(gc_page.variables.get(name) for name in ("L", "H"))
    if zl != gc or any(value in (None, "", "@", "unknown") for value in zl):
        return None
    if zl_page.variables.get("I") != "H" or gc_page.variables.get("I") != "H":
        return None
    return zl  # type: ignore[return-value]


def _candidate_corpus(
    zl_pages: Mapping[str, list[Page]],
    gc_pages: Mapping[str, list[Page]],
    stratum: tuple[str, str],
) -> tuple[tuple[str, ...], dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    zl_documents: dict[str, tuple[str, ...]] = {}
    gc_documents: dict[str, tuple[str, ...]] = {}
    for page_id in sorted(set(zl_pages) & set(gc_pages)):
        zl_page = _single_page(zl_pages, page_id)
        gc_page = _single_page(gc_pages, page_id)
        if zl_page is None or gc_page is None:
            continue
        if _known_target_stratum(zl_page, gc_page) != stratum:
            continue
        zl_tokens = _page_prose_tokens(zl_page)
        gc_tokens = _page_prose_tokens(gc_page)
        if not zl_tokens or not gc_tokens:
            continue
        zl_documents[page_id] = zl_tokens
        gc_documents[page_id] = gc_tokens
    page_ids = tuple(sorted(set(zl_documents) & set(gc_documents)))
    return (
        page_ids,
        {page: zl_documents[page] for page in page_ids},
        {page: gc_documents[page] for page in page_ids},
    )


def _manifest_locus_audit(
    pair: Mapping[str, Any],
    eva_loci: Mapping[str, list[Locus]],
    zl_loci: Mapping[str, list[Locus]],
    gc_loci: Mapping[str, list[Locus]],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    reasons: list[str] = []
    query_families: list[str] = []
    label_loci = tuple(pair.get("label_loci", ()))
    mapping_status = pair.get("mapping_status")
    if mapping_status not in {"lf_locus", "lf_loci_multi"}:
        reasons.append(str(mapping_status))
        return (), tuple(reasons)
    if not label_loci:
        reasons.append("no_predeclared_label_locus")
        return (), tuple(reasons)

    for locus_key in label_loci:
        for witness, mapping in (("EVA", eva_loci), ("ZL", zl_loci), ("GC", gc_loci)):
            candidates = mapping.get(locus_key, [])
            if len(candidates) != 1:
                reasons.append(f"{witness.lower()}_missing_or_duplicate_locus:{locus_key}")
                continue
            locus = candidates[0]
            if locus.locus_type != "Lf":
                reasons.append(f"{witness.lower()}_not_Lf:{locus_key}:{locus.locus_type}")
            if locus.locator == "!":
                reasons.append(f"{witness.lower()}_invalid_locator:{locus_key}")

        zl_candidates = zl_loci.get(locus_key, [])
        gc_candidates = gc_loci.get(locus_key, [])
        if len(zl_candidates) != 1 or len(gc_candidates) != 1:
            continue
        zl_slots = sta_family_slots(zl_candidates[0].text)
        gc_slots = sta_family_slots(gc_candidates[0].text)
        if not zl_slots or len(zl_slots) != len(gc_slots):
            reasons.append(f"component_count_mismatch:{locus_key}")
            continue
        if any(not slot.valid for slot in zl_slots):
            reasons.append(f"invalid_zl_component:{locus_key}")
            continue
        if any(not slot.valid for slot in gc_slots):
            reasons.append(f"invalid_gc_component:{locus_key}")
            continue
        zl_families = tuple(slot.family for slot in zl_slots)
        gc_families = tuple(slot.family for slot in gc_slots)
        if zl_families != gc_families:
            reasons.append(f"zl_gc_family_disagreement:{locus_key}")
            continue
        query_families.extend(family for family in zl_families if family is not None)

    return tuple(query_families), tuple(dict.fromkeys(reasons))


def build_strict_queries(
    manifest: Mapping[str, Any],
    eva: Document,
    zl: Document,
    gc: Document,
) -> tuple[tuple[StrictQuery, ...], tuple[QueryAudit, ...], dict[tuple[str, str], dict[str, Any]]]:
    if eva.header.alphabet != "Eva-":
        raise ValueError("H005 requires the pinned EVA source for mapping audit")
    if zl.header.alphabet != "STA1" or gc.header.alphabet != "STA1":
        raise ValueError("H005 requires ZL and GC STA1 sources")

    eva_loci = _locus_map(eva)
    zl_loci = _locus_map(zl)
    gc_loci = _locus_map(gc)
    zl_pages = _page_map(zl)
    gc_pages = _page_map(gc)
    corpus_cache: dict[tuple[str, str], dict[str, Any]] = {}
    queries: list[StrictQuery] = []
    audits: list[QueryAudit] = []

    for pair in manifest.get("pairs", []):
        pair_id = str(pair["pair_id"])
        target_page = str(pair["target_page"])
        target_folio = physical_folio(target_page)
        split = "holdout" if is_holdout_physical_folio(target_folio) else "discovery"
        query_families, reasons = _manifest_locus_audit(
            pair, eva_loci, zl_loci, gc_loci
        )

        zl_target = _single_page(zl_pages, target_page)
        gc_target = _single_page(gc_pages, target_page)
        stratum: tuple[str, str] | None = None
        candidate_pages: tuple[str, ...] = ()
        if zl_target is None or gc_target is None:
            reasons += ("missing_or_duplicate_target_page",)
        else:
            stratum = _known_target_stratum(zl_target, gc_target)
            if stratum is None:
                reasons += ("target_not_shared_known_herbal_stratum",)
            else:
                if stratum not in corpus_cache:
                    pages, zl_docs, gc_docs = _candidate_corpus(zl_pages, gc_pages, stratum)
                    corpus_cache[stratum] = {
                        "candidate_pages": pages,
                        "zl_tokens": zl_docs,
                        "gc_tokens": gc_docs,
                    }
                candidate_pages = corpus_cache[stratum]["candidate_pages"]
                if target_page not in candidate_pages:
                    reasons += ("target_not_in_candidate_corpus",)

        reasons = tuple(dict.fromkeys(reasons))
        admitted = bool(query_families and stratum is not None and not reasons)
        audits.append(
            QueryAudit(
                pair_id=pair_id,
                admitted=admitted,
                reasons=reasons,
                query_families=query_families,
                target_physical_folio=target_folio,
                split=split,
            )
        )
        if admitted:
            assert stratum is not None
            queries.append(
                StrictQuery(
                    pair_id=pair_id,
                    quire=str(pair["quire"]),
                    fragment_page=str(pair["fragment_page"]),
                    fragment_number=int(pair["fragment_number"]),
                    target_page=target_page,
                    target_physical_folio=target_folio,
                    strength=str(pair["strength"]),
                    label_loci=tuple(pair["label_loci"]),
                    query_families=query_families,
                    target_stratum=stratum,
                    split=split,
                    candidate_pages=candidate_pages,
                )
            )
    return tuple(queries), tuple(audits), corpus_cache


def _query_model_ranks(
    query: StrictQuery,
    model_id: str,
    corpus: Mapping[str, Any],
) -> ModelRanks:
    query_features = model_features(query.query_families, model_id)
    zl_documents = {
        page: model_features(tokens, model_id)
        for page, tokens in corpus["zl_tokens"].items()
    }
    gc_documents = {
        page: model_features(tokens, model_id)
        for page, tokens in corpus["gc_tokens"].items()
    }
    zl_scores = bm25_scores(query_features, zl_documents)
    gc_scores = bm25_scores(query_features, gc_documents)
    return ModelRanks(
        model_id=model_id,
        zl_scores=zl_scores,
        gc_scores=gc_scores,
        zl_ranks=descending_midranks(zl_scores),
        gc_ranks=descending_midranks(gc_scores),
    )


def _mean_reciprocal_rank(
    queries: Sequence[StrictQuery],
    ranks: Mapping[tuple[str, str], ModelRanks],
    model_id: str,
    target_by_pair: Mapping[str, str],
) -> float:
    if not queries:
        return 0.0
    return statistics.fmean(
        1.0 / ranks[(query.pair_id, model_id)].conservative_rank(
            target_by_pair[query.pair_id]
        )
        for query in queries
    )


def _top_three_fraction(
    queries: Sequence[StrictQuery],
    ranks: Mapping[tuple[str, str], ModelRanks],
    model_id: str,
    target_by_pair: Mapping[str, str],
) -> float:
    if not queries:
        return 0.0
    return sum(
        ranks[(query.pair_id, model_id)].conservative_rank(
            target_by_pair[query.pair_id]
        )
        <= 3.0
        for query in queries
    ) / len(queries)


def _select_model(
    discovery: Sequence[StrictQuery],
    ranks: Mapping[tuple[str, str], ModelRanks],
    targets: Mapping[str, str],
) -> tuple[str, dict[str, float]]:
    values = {
        model_id: _mean_reciprocal_rank(discovery, ranks, model_id, targets)
        for model_id in MODEL_IDS
    }
    selected = max(MODEL_IDS, key=lambda model_id: (values[model_id], -MODEL_IDS.index(model_id)))
    return selected, values


def _target_assignment(
    queries: Sequence[StrictQuery], rng: random.Random
) -> dict[str, str]:
    groups: dict[tuple[str, str], dict[str, list[StrictQuery]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for query in queries:
        groups[query.target_stratum][query.target_page].append(query)

    assignment: dict[str, str] = {}
    for stratum in sorted(groups):
        target_groups = sorted(groups[stratum])
        candidates = list(groups[stratum][target_groups[0]][0].candidate_pages)
        if len(target_groups) > len(candidates):
            raise ValueError(f"not enough candidate pages for target null stratum {stratum}")
        replacements = rng.sample(candidates, len(target_groups))
        for target_page, replacement in zip(target_groups, replacements):
            for query in groups[stratum][target_page]:
                assignment[query.pair_id] = replacement
    return assignment


def _nearest_rank(values: Sequence[float], quantile: float) -> float:
    ordered = sorted(values)
    rank = max(1, math.ceil(quantile * len(ordered)))
    return ordered[rank - 1]


def _null_metric(observed: float, null: Sequence[float]) -> dict[str, Any]:
    mean = statistics.fmean(null)
    return {
        "observed": observed,
        "null_mean": mean,
        "delta": observed - mean,
        "one_sided_monte_carlo_p": (
            1 + sum(value >= observed for value in null)
        ) / (len(null) + 1),
        "null_quantiles": {
            "q025": _nearest_rank(null, 0.025),
            "q05": _nearest_rank(null, 0.05),
            "q50": _nearest_rank(null, 0.50),
            "q95": _nearest_rank(null, 0.95),
            "q975": _nearest_rank(null, 0.975),
        },
    }


def run_h005_zg(
    queries: Sequence[StrictQuery],
    corpus_cache: Mapping[tuple[str, str], Mapping[str, Any]],
    *,
    permutations: int = PERMUTATIONS,
    seed: int = SEED,
) -> dict[str, Any]:
    if permutations < 1:
        raise ValueError("H005 permutations must be positive")
    discovery = tuple(query for query in queries if query.split == "discovery")
    holdout = tuple(query for query in queries if query.split == "holdout")
    if not discovery or not holdout:
        raise ValueError("H005 requires both discovery and holdout strict queries")

    ranks: dict[tuple[str, str], ModelRanks] = {}
    for query in queries:
        corpus = corpus_cache[query.target_stratum]
        for model_id in MODEL_IDS:
            ranks[(query.pair_id, model_id)] = _query_model_ranks(
                query, model_id, corpus
            )

    observed_targets = {query.pair_id: query.target_page for query in queries}
    selected_model, discovery_mrr = _select_model(discovery, ranks, observed_targets)
    observed_mrr = _mean_reciprocal_rank(
        holdout, ranks, selected_model, observed_targets
    )
    observed_top3 = _top_three_fraction(
        holdout, ranks, selected_model, observed_targets
    )
    quires = tuple(sorted({query.quire for query in queries}))
    observed_holdout_quire_mrr = {
        quire: _mean_reciprocal_rank(
            [query for query in holdout if query.quire == quire],
            ranks,
            selected_model,
            observed_targets,
        )
        for quire in quires
    }
    observed_discovery_quire_mrr = {
        quire: _mean_reciprocal_rank(
            [query for query in discovery if query.quire == quire],
            ranks,
            selected_model,
            observed_targets,
        )
        for quire in quires
    }
    strengths = tuple(sorted({query.strength for query in holdout}))
    observed_holdout_strength_mrr = {
        strength: _mean_reciprocal_rank(
            [query for query in holdout if query.strength == strength],
            ranks,
            selected_model,
            observed_targets,
        )
        for strength in strengths
    }
    query_forms = tuple(sorted({query.query_families for query in holdout}))
    observed_holdout_form_mrr = {
        " ".join(form): _mean_reciprocal_rank(
            [query for query in holdout if query.query_families == form],
            ranks,
            selected_model,
            observed_targets,
        )
        for form in query_forms
    }

    null_mrr: list[float] = []
    null_top3: list[float] = []
    null_holdout_quire_mrr: dict[str, list[float]] = {
        quire: [] for quire in quires
    }
    null_discovery_quire_mrr: dict[str, list[float]] = {
        quire: [] for quire in quires
    }
    null_holdout_strength_mrr: dict[str, list[float]] = {
        strength: [] for strength in strengths
    }
    null_holdout_form_mrr: dict[str, list[float]] = {
        " ".join(form): [] for form in query_forms
    }
    null_selected_models: Counter[str] = Counter()
    rng = random.Random(seed)
    for _ in range(permutations):
        null_targets = _target_assignment(queries, rng)
        null_selected, _ = _select_model(discovery, ranks, null_targets)
        null_selected_models[null_selected] += 1
        null_mrr.append(
            _mean_reciprocal_rank(holdout, ranks, null_selected, null_targets)
        )
        null_top3.append(
            _top_three_fraction(holdout, ranks, null_selected, null_targets)
        )
        for quire in quires:
            holdout_quire_queries = [
                query for query in holdout if query.quire == quire
            ]
            discovery_quire_queries = [
                query for query in discovery if query.quire == quire
            ]
            null_holdout_quire_mrr[quire].append(
                _mean_reciprocal_rank(
                    holdout_quire_queries, ranks, null_selected, null_targets
                )
            )
            null_discovery_quire_mrr[quire].append(
                _mean_reciprocal_rank(
                    discovery_quire_queries, ranks, null_selected, null_targets
                )
            )
        for strength in strengths:
            null_holdout_strength_mrr[strength].append(
                _mean_reciprocal_rank(
                    [query for query in holdout if query.strength == strength],
                    ranks,
                    null_selected,
                    null_targets,
                )
            )
        for form in query_forms:
            form_label = " ".join(form)
            null_holdout_form_mrr[form_label].append(
                _mean_reciprocal_rank(
                    [query for query in holdout if query.query_families == form],
                    ranks,
                    null_selected,
                    null_targets,
                )
            )

    pair_results: list[dict[str, Any]] = []
    for query in queries:
        model_ranks = ranks[(query.pair_id, selected_model)]
        target_rank = model_ranks.conservative_rank(query.target_page)
        conservative_order = sorted(
            query.candidate_pages,
            key=lambda page: (model_ranks.conservative_rank(page), page),
        )
        pair_results.append(
            {
                "pair_id": query.pair_id,
                "quire": query.quire,
                "split": query.split,
                "strength": query.strength,
                "fragment": f"{query.fragment_page}#{query.fragment_number}",
                "label_loci": list(query.label_loci),
                "query_families": list(query.query_families),
                "target_page": query.target_page,
                "target_physical_folio": query.target_physical_folio,
                "target_stratum_L_H": list(query.target_stratum),
                "candidate_pages": len(query.candidate_pages),
                "target_ranks": {
                    "ZL": round(model_ranks.zl_ranks[query.target_page], 8),
                    "GC": round(model_ranks.gc_ranks[query.target_page], 8),
                    "conservative": round(target_rank, 8),
                },
                "target_scores": {
                    "ZL": round(model_ranks.zl_scores[query.target_page], 8),
                    "GC": round(model_ranks.gc_scores[query.target_page], 8),
                },
                "conservative_top_five": [
                    {
                        "page_id": page,
                        "conservative_rank": round(
                            model_ranks.conservative_rank(page), 8
                        ),
                        "zl_score": round(model_ranks.zl_scores[page], 8),
                        "gc_score": round(model_ranks.gc_scores[page], 8),
                    }
                    for page in conservative_order[:5]
                ],
            }
        )

    collisions: list[dict[str, Any]] = []
    by_form: dict[tuple[str, ...], list[StrictQuery]] = defaultdict(list)
    for query in queries:
        by_form[query.query_families].append(query)
    for form, members in sorted(by_form.items()):
        target_folios = sorted({member.target_physical_folio for member in members})
        if len(target_folios) > 1:
            collisions.append(
                {
                    "query_families": list(form),
                    "pair_ids": [member.pair_id for member in members],
                    "target_physical_folios": target_folios,
                }
            )

    mrr_result = _null_metric(observed_mrr, null_mrr)
    top3_result = _null_metric(observed_top3, null_top3)
    holdout_quire_results = {
        quire: _null_metric(
            observed_holdout_quire_mrr[quire], null_holdout_quire_mrr[quire]
        )
        for quire in quires
    }
    discovery_quire_results = {
        quire: _null_metric(
            observed_discovery_quire_mrr[quire], null_discovery_quire_mrr[quire]
        )
        for quire in quires
    }
    holdout_strength_results = {
        strength: _null_metric(
            observed_holdout_strength_mrr[strength],
            null_holdout_strength_mrr[strength],
        )
        for strength in strengths
    }
    holdout_form_results = {
        form_label: _null_metric(
            observed_holdout_form_mrr[form_label],
            null_holdout_form_mrr[form_label],
        )
        for form_label in sorted(observed_holdout_form_mrr)
    }
    return {
        "model_definitions": {
            "M0": "exact STA-family-token BM25",
            "M1": "boundary-marked STA-family character 2/3-gram BM25",
            "BM25_k1": BM25_K1,
            "BM25_b": BM25_B,
        },
        "model_selection": {
            "selected_model": selected_model,
            "discovery_conservative_mrr": {
                model: round(value, 8) for model, value in discovery_mrr.items()
            },
            "tie_break_order": list(MODEL_IDS),
        },
        "permutations_requested": permutations,
        "permutations_run": permutations,
        "seed_label": SEED_LABEL,
        "seed_unsigned_big_endian_128": seed,
        "null_selected_model_counts": {
            model: null_selected_models.get(model, 0) for model in MODEL_IDS
        },
        "holdout_metrics": {
            "conservative_mrr": mrr_result,
            "top_three_fraction": top3_result,
            "by_quire_holdout_conservative_mrr": holdout_quire_results,
            "by_quire_discovery_conservative_mrr": discovery_quire_results,
            "by_source_strength_holdout_conservative_mrr": holdout_strength_results,
            "by_unique_query_form_holdout_conservative_mrr": holdout_form_results,
        },
        "query_form_collisions": collisions,
        "pair_results": pair_results,
    }


def _hash_document(document: Document) -> str:
    return sha256(document.source).hexdigest()


def build_h005_report(
    manifest_bytes: bytes,
    protocol_bytes: bytes,
    eva: Document,
    zl: Document,
    gc: Document,
    *,
    permutations: int = PERMUTATIONS,
    seed: int = SEED,
) -> dict[str, Any]:
    if sha256(manifest_bytes).hexdigest() != SOURCE_MANIFEST_SHA256:
        raise ValueError("H005 source-anchor manifest hash does not match frozen protocol")
    if _hash_document(eva) != EVA_SHA256:
        raise ValueError("H005 EVA source hash mismatch")
    if _hash_document(zl) != ZL_STA_SHA256:
        raise ValueError("H005 ZL STA1 source hash mismatch")
    if _hash_document(gc) != GC_STA_SHA256:
        raise ValueError("H005 GC STA1 source hash mismatch")

    manifest = json.loads(manifest_bytes)
    manifest_pairs = tuple(manifest.get("pairs", ()))
    raw_holdout_pairs = tuple(
        pair
        for pair in manifest_pairs
        if is_holdout_physical_folio(physical_folio(str(pair["target_page"])))
    )
    raw_holdout_folios = {
        physical_folio(str(pair["target_page"])) for pair in raw_holdout_pairs
    }
    queries, audits, corpus_cache = build_strict_queries(manifest, eva, zl, gc)
    analysis = run_h005_zg(
        queries, corpus_cache, permutations=permutations, seed=seed
    )

    strict_physical_targets = {query.target_physical_folio for query in queries}
    strict_fragment_pages = {query.fragment_page for query in queries}
    strict_quires = {query.quire for query in queries}
    holdout = [query for query in queries if query.split == "holdout"]
    holdout_folios = {query.target_physical_folio for query in holdout}
    breadth_checks = {
        "at_least_16_strict_pairs": len(queries) >= 16,
        "at_least_12_physical_targets": len(strict_physical_targets) >= 12,
        "at_least_3_pharmaceutical_pages": len(strict_fragment_pages) >= 3,
        "both_q15_and_q19": strict_quires == {"q15", "q19"},
        "at_least_5_holdout_pairs": len(holdout) >= 5,
        "at_least_5_holdout_physical_folios": len(holdout_folios) >= 5,
    }
    metrics = analysis["holdout_metrics"]
    mrr = metrics["conservative_mrr"]
    top3 = metrics["top_three_fraction"]
    holdout_quire_metrics = metrics["by_quire_holdout_conservative_mrr"]
    discovery_quire_metrics = metrics["by_quire_discovery_conservative_mrr"]
    statistical_checks = {
        "mrr_delta_at_least_0_15": mrr["delta"] >= 0.15,
        "top_three_fraction_at_least_0_60": top3["observed"] >= 0.60,
        "mrr_p_at_most_0_01": mrr["one_sided_monte_carlo_p"] <= 0.01,
        "top_three_p_at_most_0_01": top3["one_sided_monte_carlo_p"] <= 0.01,
        "positive_discovery_and_holdout_direction_in_each_quire": bool(
            holdout_quire_metrics
        )
        and set(holdout_quire_metrics) == set(discovery_quire_metrics)
        and all(item["delta"] > 0 for item in holdout_quire_metrics.values())
        and all(item["delta"] > 0 for item in discovery_quire_metrics.values()),
    }
    collision_check = not analysis["query_form_collisions"]
    breadth_gate = all(breadth_checks.values())
    statistical_gate = all(statistical_checks.values())
    zg_gate = breadth_gate and statistical_gate and collision_check

    if not breadth_gate:
        disposition = "inconclusive: strict transcription or holdout breadth failed"
    elif zg_gate:
        disposition = (
            "promising source-claim retrieval effect; authorize unchanged IT robustness "
            "but do not issue a gloss before blinded image gold"
        )
    else:
        disposition = (
            "reject H005-v1 as a q15/q19 plant-identity label retrieval route under "
            "the frozen ZL/GC source-claim benchmark"
        )

    return {
        "analysis_version": ANALYSIS_VERSION,
        "stage": "ZL/GC source-claim retrieval; pre-IT and pre-image-gold",
        "inputs": {
            "source_anchor_manifest": {
                "sha256": sha256(manifest_bytes).hexdigest(),
                "pairs": len(manifest_pairs),
            },
            "protocol": {"sha256": sha256(protocol_bytes).hexdigest()},
            "eva": {"sha256": _hash_document(eva)},
            "zl_sta1": {"sha256": _hash_document(zl)},
            "gc_sta1": {"sha256": _hash_document(gc)},
            "reserved_it_sta1": {
                "declared_sha256": RESERVED_IT_STA_SHA256,
                "opened_by_this_analysis": False,
                "parsed_by_this_analysis": False,
                "target_prose_projected_by_this_analysis": False,
            },
        },
        "manifest_audit": {
            "source_pairs": len(manifest_pairs),
            "raw_holdout_claims_before_query_gates": len(raw_holdout_pairs),
            "raw_holdout_physical_folios_before_query_gates": sorted(
                raw_holdout_folios
            ),
            "strict_queries": len(queries),
            "excluded_queries": len(audits) - len(queries),
            "strict_physical_targets": len(strict_physical_targets),
            "strict_pharmaceutical_pages": len(strict_fragment_pages),
            "strict_quires": sorted(strict_quires),
            "holdout_queries": len(holdout),
            "holdout_physical_folios": sorted(holdout_folios),
            "query_audit": [
                {
                    "pair_id": audit.pair_id,
                    "admitted": audit.admitted,
                    "reasons": list(audit.reasons),
                    "query_families": list(audit.query_families),
                    "target_physical_folio": audit.target_physical_folio,
                    "split": audit.split,
                }
                for audit in audits
            ],
        },
        "breadth_checks": breadth_checks,
        "breadth_gate_met": breadth_gate,
        "zg_analysis": analysis,
        "statistical_checks": statistical_checks,
        "statistical_gate_met": statistical_gate,
        "identity_collision_gate_met": collision_check,
        "h005_zg_gate_met": zg_gate,
        "it_robustness_authorized": zg_gate,
        "blinded_image_gold_available": False,
        "referential_gloss_authorized": False,
        "disposition": disposition,
    }


def render_h005_markdown(report: Mapping[str, Any], report_hash: str) -> str:
    audit = report["manifest_audit"]
    analysis = report["zg_analysis"]
    selection = analysis["model_selection"]
    metrics = analysis["holdout_metrics"]
    lines = [
        "# H005 pharmaceutical-plant anchor screen",
        "",
        f"Machine-readable JSON SHA-256: `{report_hash}`",
        "",
        f"Disposition: **{report['disposition']}**",
        "",
        "## Boundary",
        "",
        "This is a ZL/GC test of a frozen external source-claim universe. It did not",
        "load IT target prose and it has no blinded image gold. Even a statistical",
        "pass cannot by itself license a plant name, species, language, or translation.",
        "",
        "## Inventory",
        "",
        f"- Source pair claims: {audit['source_pairs']}",
        "- Raw fixed-split holdout before query gates: "
        f"{audit['raw_holdout_claims_before_query_gates']} claims on "
        f"{len(audit['raw_holdout_physical_folios_before_query_gates'])} folios "
        f"({', '.join(audit['raw_holdout_physical_folios_before_query_gates'])})",
        f"- Strict ZL/GC query pairs: {audit['strict_queries']}",
        f"- Strict physical target folios: {audit['strict_physical_targets']}",
        f"- Pharmaceutical source pages: {audit['strict_pharmaceutical_pages']}",
        f"- Holdout pairs: {audit['holdout_queries']}",
        f"- Holdout folios: {', '.join(audit['holdout_physical_folios'])}",
        f"- Breadth gate: {'pass' if report['breadth_gate_met'] else 'fail'}",
        "",
        "## Frozen retrieval result",
        "",
        f"- Selected discovery model: `{selection['selected_model']}`",
        "- Discovery conservative MRR: "
        + ", ".join(
            f"{model}={value:.8f}"
            for model, value in selection["discovery_conservative_mrr"].items()
        ),
        f"- Holdout conservative MRR: {metrics['conservative_mrr']['observed']:.8f}",
        f"- MRR null mean / delta / p: {metrics['conservative_mrr']['null_mean']:.8f} / "
        f"{metrics['conservative_mrr']['delta']:.8f} / "
        f"{metrics['conservative_mrr']['one_sided_monte_carlo_p']:.8f}",
        f"- Holdout top-three fraction: {metrics['top_three_fraction']['observed']:.8f}",
        f"- Top-three null mean / delta / p: {metrics['top_three_fraction']['null_mean']:.8f} / "
        f"{metrics['top_three_fraction']['delta']:.8f} / "
        f"{metrics['top_three_fraction']['one_sided_monte_carlo_p']:.8f}",
        f"- Statistical gate: {'pass' if report['statistical_gate_met'] else 'fail'}",
        f"- Identity-collision gate: {'pass' if report['identity_collision_gate_met'] else 'fail'}",
        f"- IT robustness authorized: {str(report['it_robustness_authorized']).lower()}",
        f"- Referential gloss authorized: {str(report['referential_gloss_authorized']).lower()}",
        "",
        "## MRR subgroups",
        "",
        "| Dimension | Subgroup | Split | Pairs | Observed MRR | Null mean | Delta | p |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    pair_results = analysis["pair_results"]
    quire_metric_sets = (
        (
            "discovery",
            metrics["by_quire_discovery_conservative_mrr"],
        ),
        (
            "holdout",
            metrics["by_quire_holdout_conservative_mrr"],
        ),
    )
    for split, subgroup_metrics in quire_metric_sets:
        for quire, item in sorted(subgroup_metrics.items()):
            count = sum(
                pair["split"] == split and pair["quire"] == quire
                for pair in pair_results
            )
            lines.append(
                f"| Quire | `{quire}` | {split} | {count} | "
                f"{item['observed']:.8f} | {item['null_mean']:.8f} | "
                f"{item['delta']:.8f} | {item['one_sided_monte_carlo_p']:.8f} |"
            )
    for strength, item in sorted(
        metrics["by_source_strength_holdout_conservative_mrr"].items()
    ):
        count = sum(
            pair["split"] == "holdout" and pair["strength"] == strength
            for pair in pair_results
        )
        lines.append(
            f"| Source strength | `{strength}` | holdout | {count} | "
            f"{item['observed']:.8f} | {item['null_mean']:.8f} | "
            f"{item['delta']:.8f} | {item['one_sided_monte_carlo_p']:.8f} |"
        )
    for form, item in sorted(
        metrics["by_unique_query_form_holdout_conservative_mrr"].items()
    ):
        count = sum(
            pair["split"] == "holdout"
            and " ".join(pair["query_families"]) == form
            for pair in pair_results
        )
        lines.append(
            f"| Query form | `{form}` | holdout | {count} | "
            f"{item['observed']:.8f} | {item['null_mean']:.8f} | "
            f"{item['delta']:.8f} | {item['one_sided_monte_carlo_p']:.8f} |"
        )
    lines.extend(
        [
        "",
        "## Held-out pairs",
        "",
        "| Pair | Query family | Target | ZL rank | GC rank | Worse rank |",
        "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for pair in pair_results:
        if pair["split"] != "holdout":
            continue
        ranks = pair["target_ranks"]
        lines.append(
            f"| `{pair['pair_id']}` | `{' '.join(pair['query_families'])}` | "
            f"{pair['target_page']} | {ranks['ZL']:.1f} | {ranks['GC']:.1f} | "
            f"{ranks['conservative']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Query-form collisions",
            "",
        ]
    )
    collisions = analysis["query_form_collisions"]
    if collisions:
        for collision in collisions:
            lines.append(
                "- `"
                + " ".join(collision["query_families"])
                + "` labels distinct target folios: "
                + ", ".join(collision["target_physical_folios"])
                + "."
            )
    else:
        lines.append("- None in the strict query set.")
    lines.extend(
        [
            "",
            "## Gate checks",
            "",
        ]
    )
    for name, passed in sorted(report["breadth_checks"].items()):
        lines.append(f"- {'PASS' if passed else 'FAIL'} `{name}`")
    for name, passed in sorted(report["statistical_checks"].items()):
        lines.append(f"- {'PASS' if passed else 'FAIL'} `{name}`")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A favorable page rank would support only a relation between one frozen Lf",
            "form and one claimed depicted entity. The route remains pre-semantic until",
            "the text-blind image benchmark passes. Failures here reject only this frozen",
            "q15/q19 identity-label retrieval route, not every possible label function.",
            "",
        ]
    )
    return "\n".join(lines)
