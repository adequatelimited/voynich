"""Reproducible corpus baselines and pre-registered structural tests."""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import math
import re
from typing import Any, Iterable, Literal

from .ivtff import Document, Locus, Page, Paragraph, iter_paragraphs, tokenize_certain_basic_eva


_FREE_COMMENT_RE = re.compile(r"<![^>]*>")
_INLINE_COMMENT_RE = re.compile(r"<[^>]*>")
_ALTERNATIVE_RE = re.compile(r"\[([^\]]*)\]")
_LIGATURE_RE = re.compile(r"\{([^{}]*)\}")
_HIGH_ASCII_RE = re.compile(r"@\d{3};")


def _require_extended_eva(document: Document, analysis_name: str) -> None:
    if document.header.alphabet != "Eva-":
        raise ValueError(
            f"{analysis_name} requires an Eva- IVTFF document; got "
            f"{document.header.alphabet!r}"
        )


def _first_alternative(match: re.Match[str]) -> str:
    return match.group(1).split(":", 1)[0]


def normalized_text(
    text: str,
    *,
    uncertain_space: Literal["boundary", "join", "retain"] = "retain",
    alternatives: Literal["first", "retain"] = "first",
    flatten_ligatures: bool = True,
) -> str:
    """Create an explicitly parameterized analytical view of locus text."""

    value = text.replace("<->", ".").replace("<~>", ".")
    value = _INLINE_COMMENT_RE.sub("", value)
    if alternatives == "first":
        value = _ALTERNATIVE_RE.sub(_first_alternative, value)
    if flatten_ligatures:
        while _LIGATURE_RE.search(value):
            value = _LIGATURE_RE.sub(r"\1", value)
    value = re.sub(r"\s+", "", value)
    if uncertain_space == "boundary":
        value = value.replace(",", ".")
    elif uncertain_space == "join":
        value = value.replace(",", "")
    return value


def word_units(
    locus: Locus,
    *,
    uncertain_space: Literal["boundary", "join"],
) -> tuple[str, ...]:
    """Return all transcribed word units under one declared space policy."""

    text = normalized_text(locus.text, uncertain_space=uncertain_space)
    return tuple(component for component in text.split(".") if component)


def sta1_glyphs(locus: Locus) -> tuple[str, ...]:
    """Return two-character STA1 glyph codes using first-alternative policy."""

    text = normalized_text(locus.text, uncertain_space="join")
    text = text.replace(".", "")
    glyphs = tuple(re.findall(r"[A-Z][0-9a-z]", text))
    residue = re.sub(r"[A-Z][0-9a-z]", "", text)
    if residue:
        raise ValueError(f"unparsed STA1 residue in {locus.identifier}: {residue!r}")
    return glyphs


def sta1_certain_word_families(locus: Locus) -> tuple[str, ...]:
    """Return unambiguous STA1 words reduced to glyph-family sequences."""

    value = locus.text.replace("<->", ".").replace("<~>", ".")
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
        codes = re.findall(r"[A-Z][0-9a-z]", component)
        if not codes or "".join(codes) != component:
            continue
        words.append("".join(code[0] for code in codes))
    return tuple(words)


def _sta1_certain_words_by_component(locus: Locus) -> tuple[str | None, ...]:
    """Return strict STA1 words while retaining their dot-component indexes.

    ``None`` marks a component that cannot support an exact member comparison:
    uncertain spaces, alternative readings, unreadable glyphs, or malformed
    STA1 content. This is intentionally stricter than choosing a preferred
    alternative because H002 needs a fail-closed positional audit.
    """

    value = locus.text.replace("<->", ".").replace("<~>", ".")
    value = _INLINE_COMMENT_RE.sub("", value)
    while _LIGATURE_RE.search(value):
        value = _LIGATURE_RE.sub(r"\1", value)
    value = re.sub(r"\s+", "", value)

    words: list[str | None] = []
    for component in value.split("."):
        if not component:
            continue
        if any(marker in component for marker in (",", "[", "]", "?", "Z1")):
            words.append(None)
            continue
        codes = re.findall(r"[A-Z][0-9a-z]", component)
        words.append("".join(codes) if codes and "".join(codes) == component else None)
    return tuple(words)


def corpus_integrity(document: Document) -> dict[str, Any]:
    loci = document.loci
    substantive = [locus for locus in loci if locus.locator != "!"]
    locus_text = "\n".join(locus.text for locus in loci)
    no_free_comments = _FREE_COMMENT_RE.sub("", locus_text)

    generic_counts = Counter(locus.generic_type for locus in loci)
    return {
        "alphabet": document.header.alphabet,
        "format_version": document.header.version,
        "source_sha256": sha256(document.source).hexdigest(),
        "retained_source_sha256": sha256(document.emit()).hexdigest(),
        "source_bytes_retained": document.emit() == document.source,
        "physical_lines": len(document.source.splitlines()),
        "page_panel_records": len(document.pages),
        "loci": len(loci),
        "substantive_loci": len(substantive),
        "invalid_locator_loci": len(loci) - len(substantive),
        "locus_families": {
            kind: generic_counts.get(kind, 0) for kind in ("P", "L", "C", "R")
        },
        "paragraph_starts": sum(locus.paragraph_start for locus in loci),
        "paragraph_ends": sum(locus.paragraph_end for locus in loci),
        "alternative_groups": len(_ALTERNATIVE_RE.findall(no_free_comments)),
        "uncertain_spaces": no_free_comments.count(","),
        "drawing_boundaries": {
            "aligned": locus_text.count("<->"),
            "misaligned": locus_text.count("<~>"),
        },
        "ligature_groups": len(_LIGATURE_RE.findall(no_free_comments)),
        "extended_eva_codes": len(_HIGH_ASCII_RE.findall(no_free_comments)),
        "tokens_comma_as_boundary": sum(
            len(word_units(locus, uncertain_space="boundary")) for locus in substantive
        ),
        "tokens_comma_joined": sum(
            len(word_units(locus, uncertain_space="join")) for locus in substantive
        ),
    }


def _certain_tokens(locus: Locus) -> tuple[str, ...]:
    return tokenize_certain_basic_eva(locus.text).tokens


def _stratum_summary(document: Document, variable: str) -> dict[str, dict[str, int]]:
    result: dict[str, Counter[str]] = defaultdict(Counter)
    for locus in document.loci:
        if locus.locator == "!":
            continue
        value = locus.effective_variables.get(variable, "unknown")
        result[value]["loci"] += 1
        result[value]["certain_basic_eva_tokens"] += len(_certain_tokens(locus))
    return {value: dict(counts) for value, counts in sorted(result.items())}


def stratified_summary(document: Document) -> dict[str, Any]:
    return {
        "currier_language": _stratum_summary(document, "L"),
        "hand": _stratum_summary(document, "H"),
        "illustration_type": _stratum_summary(document, "I"),
        "locus_family": {
            kind: {
                "loci": sum(
                    locus.generic_type == kind and locus.locator != "!"
                    for locus in document.loci
                ),
                "certain_basic_eva_tokens": sum(
                    len(_certain_tokens(locus))
                    for locus in document.loci
                    if locus.generic_type == kind and locus.locator != "!"
                ),
            }
            for kind in ("P", "L", "C", "R")
        },
    }


def _held_out_page(page_id: str) -> bool:
    # Fixed, page-level 20% split. Prefix makes the partition versioned.
    digest = sha256(f"H001-v1:{page_id}".encode("ascii")).digest()
    return digest[0] < 51


def _log2_odds(
    initial_count: int,
    token_count: int,
    initial_positions: int,
    total_positions: int,
) -> float:
    noninitial_count = token_count - initial_count
    noninitial_positions = total_positions - initial_positions
    initial_other = initial_positions - initial_count
    noninitial_other = noninitial_positions - noninitial_count
    odds = ((initial_count + 0.5) / (initial_other + 0.5)) / (
        (noninitial_count + 0.5) / (noninitial_other + 0.5)
    )
    return math.log2(odds)


def _paragraph_position_counts(paragraphs: Iterable[Paragraph]) -> dict[str, Any]:
    all_tokens: Counter[str] = Counter()
    initial_tokens: Counter[str] = Counter()
    total_positions = 0
    initial_positions = 0
    eligible_paragraphs = 0
    excluded_initials = 0

    for paragraph in paragraphs:
        components = paragraph.components()
        accepted = [component.token for component in components if component.token is not None]
        all_tokens.update(accepted)
        total_positions += len(accepted)
        if not components:
            continue
        if components[0].token is None:
            excluded_initials += 1
            continue
        initial_tokens[components[0].token] += 1
        initial_positions += 1
        eligible_paragraphs += 1

    return {
        "all_tokens": all_tokens,
        "initial_tokens": initial_tokens,
        "total_positions": total_positions,
        "initial_positions": initial_positions,
        "eligible_paragraphs": eligible_paragraphs,
        "excluded_uncertain_initials": excluded_initials,
    }


def paragraph_initial_hypothesis(document: Document) -> dict[str, Any]:
    """Test H001 on a page-level held-out partition.

    The literature-derived test is enrichment of EVA gallows-initial forms
    (``k``, ``t``, ``p``, ``f``). A separate whole-token scan is exploratory:
    discovery requires total count >= 20, paragraph-initial count >= 3, and
    smoothed log2 odds >= 1.5. Passing the descriptive held-out directional
    screen requires at least one observed initial occurrence plus positive odds.
    No semantic gloss is assigned by either test.
    """

    _require_extended_eva(document, "H001")
    paragraphs = list(iter_paragraphs(document))
    discovery = [p for p in paragraphs if not _held_out_page(p.page_id)]
    held_out = [p for p in paragraphs if _held_out_page(p.page_id)]
    discovery_counts = _paragraph_position_counts(discovery)
    held_out_counts = _paragraph_position_counts(held_out)

    def gallows_feature(counts: dict[str, Any]) -> dict[str, Any]:
        token_count = sum(
            count
            for token, count in counts["all_tokens"].items()
            if token.startswith(("k", "t", "p", "f"))
        )
        initial_count = sum(
            count
            for token, count in counts["initial_tokens"].items()
            if token.startswith(("k", "t", "p", "f"))
        )
        odds = _log2_odds(
            initial_count,
            token_count,
            counts["initial_positions"],
            counts["total_positions"],
        )
        return {
            "total": token_count,
            "initial": initial_count,
            "initial_positions": counts["initial_positions"],
            "all_positions": counts["total_positions"],
            "initial_rate": round(initial_count / counts["initial_positions"], 4),
            "background_rate": round(
                (token_count - initial_count)
                / (counts["total_positions"] - counts["initial_positions"]),
                4,
            ),
            "log2_odds": round(odds, 3),
        }

    discovery_feature = gallows_feature(discovery_counts)
    held_out_feature = gallows_feature(held_out_counts)

    candidates: list[dict[str, Any]] = []
    for token, count in discovery_counts["all_tokens"].items():
        initial = discovery_counts["initial_tokens"][token]
        odds = _log2_odds(
            initial,
            count,
            discovery_counts["initial_positions"],
            discovery_counts["total_positions"],
        )
        if count < 20 or initial < 3 or odds < 1.5:
            continue

        held_count = held_out_counts["all_tokens"][token]
        held_initial = held_out_counts["initial_tokens"][token]
        held_odds = _log2_odds(
            held_initial,
            held_count,
            held_out_counts["initial_positions"],
            held_out_counts["total_positions"],
        )
        candidates.append(
            {
                "token": token,
                "discovery_total": count,
                "discovery_initial": initial,
                "discovery_log2_odds": round(odds, 3),
                "held_out_total": held_count,
                "held_out_initial": held_initial,
                "held_out_log2_odds": round(held_odds, 3),
                "held_out_direction_positive": held_initial >= 1 and held_odds > 0,
            }
        )

    candidates.sort(
        key=lambda item: (item["discovery_log2_odds"], item["discovery_initial"]),
        reverse=True,
    )
    return {
        "hypothesis_id": "H001",
        "claim_scope": "gallows-initial paragraph-position enrichment only; no semantics",
        "split": "SHA256('H001-v1:' + page_id), first byte < 51 is held out",
        "discovery_pages": len({p.page_id for p in discovery}),
        "held_out_pages": len({p.page_id for p in held_out}),
        "discovery": {
            key: value
            for key, value in discovery_counts.items()
            if not isinstance(value, Counter)
        },
        "held_out": {
            key: value
            for key, value in held_out_counts.items()
            if not isinstance(value, Counter)
        },
        "literature_derived_feature": {
            "definition": "accepted basic-EVA token starts with k, t, p, or f",
            "discovery": discovery_feature,
            "held_out": held_out_feature,
            "held_out_direction_positive": held_out_feature["initial"] >= 1
            and held_out_feature["log2_odds"] > 0,
        },
        "exploratory_selection_rule": "discovery total>=20, initial>=3, log2_odds>=1.5",
        "exploratory_whole_token_candidates": candidates,
        "exploratory_held_out_positive_direction_count": sum(
            item["held_out_direction_positive"] for item in candidates
        ),
    }


_TRUE_LABEL_TYPES = frozenset({"La", "Lc", "Lf", "Ln", "Lp", "Ls", "Lt", "Lz"})


def _h002_held_out(page_id: str) -> bool:
    digest = sha256(f"H002-v1:{page_id}".encode("ascii")).digest()
    return digest[0] < 51


def _single_page_value(page: Page, variable: str, relevant: list[Locus]) -> str | None:
    values = {
        locus.effective_variables.get(variable)
        for locus in relevant
        if locus.effective_variables.get(variable) is not None
    }
    if len(values) != 1:
        return None
    return next(iter(values))


def _h002_page_record(page: Page) -> dict[str, Any] | None:
    labels = {
        token
        for locus in page.loci
        if locus.locator != "!" and locus.locus_type in _TRUE_LABEL_TYPES
        for token in _certain_tokens(locus)
    }
    prose = {
        token
        for locus in page.loci
        if locus.locator != "!" and locus.generic_type == "P"
        for token in _certain_tokens(locus)
    }
    if not labels or not prose:
        return None

    relevant = [
        locus
        for locus in page.loci
        if locus.locator != "!"
        and (locus.locus_type in _TRUE_LABEL_TYPES or locus.generic_type == "P")
    ]
    stratum_values = tuple(_single_page_value(page, variable, relevant) for variable in "ILH")
    if any(value is None for value in stratum_values):
        return None
    return {
        "page_id": page.page_id,
        "stratum": stratum_values,
        "label_types": labels,
        "prose_types": prose,
    }


def _h002_split_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_stratum: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_stratum[record["stratum"]].append(record)

    page_results: list[dict[str, Any]] = []
    local_hits: list[dict[str, str]] = []
    observed_total = 0
    expected_total = 0.0
    evaluated_total = 0

    for record in sorted(records, key=lambda item: item["page_id"]):
        peers = [
            peer
            for peer in by_stratum[record["stratum"]]
            if peer["page_id"] != record["page_id"]
        ]
        if not peers:
            continue

        observed = sum(token in record["prose_types"] for token in record["label_types"])
        expected = sum(
            sum(token in peer["prose_types"] for peer in peers) / len(peers)
            for token in record["label_types"]
        )
        count = len(record["label_types"])
        score = (observed - expected) / count
        page_results.append(
            {
                "page_id": record["page_id"],
                "stratum_I_L_H": list(record["stratum"]),
                "label_types": count,
                "observed_local_hits": observed,
                "expected_peer_hits": round(expected, 4),
                "enrichment": round(score, 4),
            }
        )
        for token in sorted(record["label_types"] & record["prose_types"]):
            local_hits.append({"page_id": record["page_id"], "token": token})
        observed_total += observed
        expected_total += expected
        evaluated_total += count

    observed_rate = observed_total / evaluated_total if evaluated_total else 0.0
    expected_rate = expected_total / evaluated_total if evaluated_total else 0.0
    return {
        "pages_with_peers": len(page_results),
        "evaluated_label_types": evaluated_total,
        "observed_local_hits": observed_total,
        "expected_peer_hits": round(expected_total, 4),
        "observed_rate": round(observed_rate, 4),
        "expected_rate": round(expected_rate, 4),
        "enrichment": round(observed_rate - expected_rate, 4),
        "positive_page_scores": sum(page["enrichment"] > 0 for page in page_results),
        "zero_page_scores": sum(page["enrichment"] == 0 for page in page_results),
        "negative_page_scores": sum(page["enrichment"] < 0 for page in page_results),
        "local_hits": local_hits,
        "pages": page_results,
    }


def local_label_recurrence_hypothesis(document: Document) -> dict[str, Any]:
    """Run frozen H002: exact true-label recurrence in same-page prose."""

    _require_extended_eva(document, "H002")
    records = [record for page in document.pages if (record := _h002_page_record(page))]
    discovery_records = [record for record in records if not _h002_held_out(record["page_id"])]
    held_out_records = [record for record in records if _h002_held_out(record["page_id"])]
    discovery = _h002_split_report(discovery_records)
    held_out = _h002_split_report(held_out_records)
    enough_label_types = held_out["evaluated_label_types"] >= 10
    within_zl_criterion_met = enough_label_types and held_out["enrichment"] > 0
    return {
        "hypothesis_id": "H002",
        "claim_scope": "exact certain-EVA label-type recurrence in local prose; no gloss",
        "true_label_types": sorted(_TRUE_LABEL_TYPES),
        "stratum": ["illustration_type_I", "Currier_L", "hand_H"],
        "peer_scope": "same split and same I/L/H; own page excluded",
        "split": "SHA256('H002-v1:' + page_id), first byte < 51 is held out",
        "eligible_records_before_peer_filter": len(records),
        "discovery": discovery,
        "held_out": held_out,
        "primary_criterion": "held-out enrichment > 0 with at least 10 evaluated label types",
        "enough_label_types_under_frozen_rule": enough_label_types,
        "held_out_evaluation_units": {
            "unit": "page",
            "count": held_out["pages_with_peers"],
        },
        "interpretation": "descriptive within-ZL screen; not an inferential result",
        "within_zl_primary_criterion_met": within_zl_criterion_met,
        "independent_transcription_validation_required": True,
        "disposition": (
            "numeric screen passed; do not use as a crib without independent transcription validation"
            if within_zl_criterion_met
            else "within-ZL numeric screen failed; do not use as a translation crib"
        ),
    }


def _h003_partition_b(page_id: str) -> bool:
    digest = sha256(f"H003-v1:{page_id}".encode("ascii")).digest()
    return digest[0] < 64


def _locus_map(document: Document) -> dict[tuple[str, int], Locus]:
    result: dict[tuple[str, int], Locus] = {}
    for locus in document.loci:
        if locus.locator == "!":
            continue
        key = (locus.page_id, locus.number)
        if key in result:
            raise ValueError(f"duplicate substantive locus key: {key!r}")
        result[key] = locus
    return result


def _h002_eva_occurrences(
    document: Document, page_id: str, token: str, role: Literal["label", "prose"]
) -> list[tuple[Locus, int]]:
    """Locate exact certain-EVA hits and retain their dot-component indexes."""

    occurrences: list[tuple[Locus, int]] = []
    for page in document.pages:
        if page.page_id != page_id:
            continue
        for locus in page.loci:
            if locus.locator == "!":
                continue
            if role == "label" and locus.locus_type not in _TRUE_LABEL_TYPES:
                continue
            if role == "prose" and locus.generic_type != "P":
                continue
            for component_index, component in enumerate(
                tokenize_certain_basic_eva(locus.text).components
            ):
                if component.token == token:
                    occurrences.append((locus, component_index))
        break
    return occurrences


def _sta1_family(word: str | None) -> str | None:
    if word is None:
        return None
    return "".join(code[0] for code in re.findall(r"[A-Z][0-9a-z]", word))


def h002_cross_transcription_sta1_audit(
    eva: Document,
    zl_sta: Document,
    gc_sta: Document,
    *,
    h002_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit held-out H002 hits at the same locus and component index.

    The audit enumerates every certain-EVA label/prose occurrence belonging to
    each held-out local hit. It then reads the word at the identical zero-based
    dot-component index in the aligned ZL and GC STA1 loci. Exact member and
    glyph-family comparisons are reported separately for every label/prose
    occurrence pair; missing, structurally mismatched, or uncertain alignments
    never count as matches.
    """

    _require_extended_eva(eva, "H002 STA1 audit")
    if zl_sta.header.alphabet != "STA1" or gc_sta.header.alphabet != "STA1":
        raise ValueError("H002 STA1 audit requires two STA1 documents")

    report = h002_report or local_label_recurrence_hypothesis(eva)
    if report.get("hypothesis_id") != "H002":
        raise ValueError("H002 STA1 audit requires an H002 report")

    zl_loci = _locus_map(zl_sta)
    gc_loci = _locus_map(gc_sta)

    def aligned_occurrence(
        locus: Locus, component_index: int, role: Literal["label", "prose"]
    ) -> dict[str, Any]:
        key = (locus.page_id, locus.number)
        zl_locus = zl_loci.get(key)
        gc_locus = gc_loci.get(key)
        result: dict[str, Any] = {
            "role": role,
            "eva_locus": locus.identifier,
            "component_index": component_index,
            "index_basis": "zero-based nonempty dot/drawing-boundary component",
            "zl_sta1_word": None,
            "gc_sta1_word": None,
            "zl_family": None,
            "gc_family": None,
            "exact_word_agrees_between_transcriptions": False,
            "family_agrees_between_transcriptions": False,
            "alignment_status": "missing_sta1_locus",
        }
        if zl_locus is None or gc_locus is None:
            return result
        if (
            zl_locus.locus_type != locus.locus_type
            or gc_locus.locus_type != locus.locus_type
            or zl_locus.locator != locus.locator
            or gc_locus.locator != locus.locator
        ):
            result["alignment_status"] = "locus_metadata_mismatch"
            return result

        zl_words = _sta1_certain_words_by_component(zl_locus)
        gc_words = _sta1_certain_words_by_component(gc_locus)
        if component_index >= len(zl_words) or component_index >= len(gc_words):
            result["alignment_status"] = "component_index_out_of_range"
            return result

        zl_word = zl_words[component_index]
        gc_word = gc_words[component_index]
        zl_family = _sta1_family(zl_word)
        gc_family = _sta1_family(gc_word)
        result.update(
            {
                "zl_sta1_word": zl_word,
                "gc_sta1_word": gc_word,
                "zl_family": zl_family,
                "gc_family": gc_family,
                "exact_word_agrees_between_transcriptions": (
                    zl_word is not None and zl_word == gc_word
                ),
                "family_agrees_between_transcriptions": (
                    zl_family is not None and zl_family == gc_family
                ),
                "alignment_status": (
                    "aligned_certain"
                    if zl_word is not None and gc_word is not None
                    else "uncertain_sta1_component"
                ),
            }
        )
        return result

    audited_hits: list[dict[str, Any]] = []
    for hit in report["held_out"]["local_hits"]:
        page_id = hit["page_id"]
        token = hit["token"]
        label_occurrences = [
            aligned_occurrence(locus, index, "label")
            for locus, index in _h002_eva_occurrences(eva, page_id, token, "label")
        ]
        prose_occurrences = [
            aligned_occurrence(locus, index, "prose")
            for locus, index in _h002_eva_occurrences(eva, page_id, token, "prose")
        ]

        comparisons: list[dict[str, Any]] = []
        for label in label_occurrences:
            for prose in prose_occurrences:
                zl_exact = (
                    label["zl_sta1_word"] is not None
                    and label["zl_sta1_word"] == prose["zl_sta1_word"]
                )
                gc_exact = (
                    label["gc_sta1_word"] is not None
                    and label["gc_sta1_word"] == prose["gc_sta1_word"]
                )
                zl_family = (
                    label["zl_family"] is not None
                    and label["zl_family"] == prose["zl_family"]
                )
                gc_family = (
                    label["gc_family"] is not None
                    and label["gc_family"] == prose["gc_family"]
                )
                comparisons.append(
                    {
                        "label_locus": label["eva_locus"],
                        "label_component_index": label["component_index"],
                        "prose_locus": prose["eva_locus"],
                        "prose_component_index": prose["component_index"],
                        "exact_member_match": {
                            "zl": zl_exact,
                            "gc": gc_exact,
                            "supported_by_both_transcriptions": zl_exact and gc_exact,
                        },
                        "family_match": {
                            "zl": zl_family,
                            "gc": gc_family,
                            "supported_by_both_transcriptions": zl_family and gc_family,
                        },
                    }
                )

        alignment_complete = bool(label_occurrences and prose_occurrences) and all(
            occurrence["alignment_status"] == "aligned_certain"
            for occurrence in label_occurrences + prose_occurrences
        )
        audited_hits.append(
            {
                "page_id": page_id,
                "eva_token": token,
                "label_occurrences": label_occurrences,
                "prose_occurrences": prose_occurrences,
                "pair_comparisons": comparisons,
                "alignment_complete": alignment_complete,
                "any_pair_exact_member_supported_by_both_transcriptions": any(
                    pair["exact_member_match"]["supported_by_both_transcriptions"]
                    for pair in comparisons
                ),
                "any_pair_family_supported_by_both_transcriptions": any(
                    pair["family_match"]["supported_by_both_transcriptions"]
                    for pair in comparisons
                ),
            }
        )

    return {
        "input_sha256": {
            "eva": sha256(eva.source).hexdigest(),
            "zl_sta1": sha256(zl_sta.source).hexdigest(),
            "gc_sta1_level0": sha256(gc_sta.source).hexdigest(),
        },
        "matching_rule": (
            "map every exact certain-EVA occurrence to the same page, locus number, "
            "and zero-based nonempty dot/drawing-boundary component in ZL and GC STA1"
        ),
        "uncertainty_policy": (
            "missing loci, locus metadata mismatches, out-of-range indexes, uncertain "
            "spaces, alternatives, unreadable glyphs, and malformed STA1 fail closed"
        ),
        "hits": audited_hits,
        "summary": {
            "held_out_hits_audited": len(audited_hits),
            "all_alignments_complete": bool(audited_hits)
            and all(
                hit["alignment_complete"] for hit in audited_hits
            ),
            "hits_with_exact_member_support_in_both_transcriptions": sum(
                hit["any_pair_exact_member_supported_by_both_transcriptions"]
                for hit in audited_hits
            ),
            "hits_with_family_support_in_both_transcriptions": sum(
                hit["any_pair_family_supported_by_both_transcriptions"]
                for hit in audited_hits
            ),
            "all_hits_have_exact_member_support_in_both_transcriptions": bool(
                audited_hits
            )
            and all(
                hit["any_pair_exact_member_supported_by_both_transcriptions"]
                for hit in audited_hits
            ),
            "all_hits_have_family_support_in_both_transcriptions": bool(audited_hits)
            and all(
                hit["any_pair_family_supported_by_both_transcriptions"]
                for hit in audited_hits
            ),
        },
    }


def _alignment_inventory(zl: Document, gc: Document) -> dict[str, Any]:
    zl_map = _locus_map(zl)
    gc_map = _locus_map(gc)
    common = sorted(zl_map.keys() & gc_map.keys())
    return {
        "zl_substantive_loci": len(zl_map),
        "gc_substantive_loci": len(gc_map),
        "common_loci": len(common),
        "zl_only_loci": len(zl_map.keys() - gc_map.keys()),
        "gc_only_loci": len(gc_map.keys() - zl_map.keys()),
        "locus_type_mismatches": sum(
            zl_map[key].locus_type != gc_map[key].locus_type for key in common
        ),
        "locator_mismatches": sum(
            zl_map[key].locator != gc_map[key].locator for key in common
        ),
    }


def _h003_page_records(zl: Document, gc: Document) -> list[dict[str, Any]]:
    gc_loci = _locus_map(gc)
    records: list[dict[str, Any]] = []
    for page in zl.pages:
        label_types: set[str] = set()
        prose_types: set[str] = set()
        relevant: list[Locus] = []
        for locus in page.loci:
            if locus.locator == "!":
                continue
            is_label = locus.locus_type in _TRUE_LABEL_TYPES
            is_prose = locus.generic_type == "P"
            if not is_label and not is_prose:
                continue
            peer = gc_loci.get((locus.page_id, locus.number))
            if peer is None or peer.locator == "!":
                continue
            if peer.locus_type != locus.locus_type or peer.locator != locus.locator:
                continue
            shared_types = set(sta1_certain_word_families(locus)) & set(
                sta1_certain_word_families(peer)
            )
            if is_label:
                label_types.update(shared_types)
            if is_prose:
                prose_types.update(shared_types)
            relevant.append(locus)

        if not label_types or not prose_types or not relevant:
            continue
        stratum = tuple(_single_page_value(page, variable, relevant) for variable in "ILH")
        if any(value is None for value in stratum):
            continue
        records.append(
            {
                "page_id": page.page_id,
                "stratum": stratum,
                "label_types": label_types,
                "prose_types": prose_types,
            }
        )
    return records


def locus_shared_family_label_recurrence_hypothesis(
    zl_sta: Document, gc_sta: Document
) -> dict[str, Any]:
    """Run retrospective H003 on locus-shared STA-family type sets."""

    if zl_sta.header.alphabet != "STA1" or gc_sta.header.alphabet != "STA1":
        raise ValueError("H003 requires STA1 inputs")
    records = _h003_page_records(zl_sta, gc_sta)
    partition_a_records = [
        record for record in records if not _h003_partition_b(record["page_id"])
    ]
    partition_b_records = [
        record for record in records if _h003_partition_b(record["page_id"])
    ]
    partition_a = _h002_split_report(partition_a_records)
    partition_b = _h002_split_report(partition_b_records)
    breadth_ok = partition_b["pages_with_peers"] >= 5
    count_ok = partition_b["evaluated_label_types"] >= 30
    direction_ok = partition_b["enrichment"] > 0
    page_sign_ok = partition_b["positive_page_scores"] > partition_b["negative_page_scores"]
    advancement_criterion_met = breadth_ok and count_ok and direction_ok and page_sign_ok
    partition_b_pages = [page["page_id"] for page in partition_b["pages"]]
    prior_h002_discovery = [page for page in partition_b_pages if not _h002_held_out(page)]
    prior_h002_held_out = [page for page in partition_b_pages if _h002_held_out(page)]
    return {
        "hypothesis_id": "H003",
        "claim_scope": "locus-shared STA-family type recurrence; no token alignment, allography, or gloss claim",
        "input_sha256": {
            "zl_sta1": sha256(zl_sta.source).hexdigest(),
            "gc_sta1_level0": sha256(gc_sta.source).hexdigest(),
        },
        "alignment": _alignment_inventory(zl_sta, gc_sta),
        "partition": "SHA256('H003-v1:' + page_id), first byte < 64 enters partition B",
        "partition_validity": (
            "retrospective exploratory partition defined after H002 output was inspected; "
            "partition B is not an untouched holdout"
        ),
        "prior_h002_partition_overlap": {
            "partition_b_pages_with_peers": partition_b_pages,
            "also_h002_discovery_pages": prior_h002_discovery,
            "also_h002_held_out_pages": prior_h002_held_out,
        },
        "matching_semantics": (
            "unordered family-type set intersection within an aligned locus; not positional word agreement"
        ),
        "peer_scope": "same retrospective partition and same I/L/H; own page excluded",
        "eligible_records_before_peer_filter": len(records),
        "partition_a": partition_a,
        "partition_b": partition_b,
        "frozen_advancement_criterion": (
            "partition-B enrichment>0, >=5 pages with peers, >=30 label types, "
            "and positive page scores > negative page scores"
        ),
        "criterion_checks": {
            "minimum_page_breadth_met": breadth_ok,
            "minimum_label_count_met": count_ok,
            "enrichment_direction_ok": direction_ok,
            "page_sign_ok": page_sign_ok,
        },
        "minimum_breadth_met": breadth_ok and count_ok,
        "advancement_criterion_met": advancement_criterion_met,
        "disposition": (
            "eligible only for a new sealed or external confirmation test"
            if advancement_criterion_met
            else "do not advance this crib; absence is not established"
        ),
    }


def baseline_report(
    document: Document,
    *,
    top_n: int = 30,
    zl_sta_document: Document | None = None,
    gc_sta_document: Document | None = None,
) -> dict[str, Any]:
    _require_extended_eva(document, "baseline_report")
    tokens = [
        token
        for locus in document.loci
        if locus.locator != "!"
        for token in _certain_tokens(locus)
    ]
    excluded = Counter(
        excluded.reason
        for locus in document.loci
        if locus.locator != "!"
        for excluded in tokenize_certain_basic_eva(locus.text).excluded
    )
    frequencies = Counter(tokens)
    h002 = local_label_recurrence_hypothesis(document)
    hypotheses: dict[str, Any] = {
        "H001": paragraph_initial_hypothesis(document),
        "H002": h002,
    }
    if zl_sta_document is not None and gc_sta_document is not None:
        h002["cross_transcription_sta1_audit"] = h002_cross_transcription_sta1_audit(
            document,
            zl_sta_document,
            gc_sta_document,
            h002_report=h002,
        )
        hypotheses["H003"] = locus_shared_family_label_recurrence_hypothesis(
            zl_sta_document, gc_sta_document
        )
    return {
        "integrity": corpus_integrity(document),
        "conservative_basic_eva": {
            "accepted_tokens": len(tokens),
            "types": len(frequencies),
            "excluded_components": sum(excluded.values()),
            "exclusion_reasons": dict(excluded.most_common()),
            "top_tokens": [
                {"token": token, "count": count}
                for token, count in frequencies.most_common(top_n)
            ],
        },
        "strata": stratified_summary(document),
        "hypotheses": hypotheses,
    }
