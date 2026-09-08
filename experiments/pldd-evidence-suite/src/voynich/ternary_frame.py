"""Frozen H006-FR3-LINE-v1 fixed-three-trit frame screen.

The frame screen is deliberately key- and plaintext-free.  It admits only
exact ZL/IT Basic-EVA line consensus, applies either of the two frozen
recursive component tables, and tests the deterministic line-length
invariant.  Held-out tokens are not expanded unless a discovery model has
zero contradictions and the non-residue holdout breadth gate also passes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from .ivtff import Document, Locus, parse_ivtff, tokenize_certain_basic_eva


ANALYSIS_VERSION = "H006-FR3-LINE-v1"
MODEL_IDS = ("PAIR", "OPTIONAL_E")

ZL_EVA_SHA256 = "bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc"
IT_EVA_SHA256 = "7f27a8b0feed8f6de0a99900df6bf912dd1d295c38e5f830bac8b41c3f536fb5"
PROTOCOL_SHA256 = "88e75dd64fa0af6554a613b7d0d1120619f63d18785133febfeb0bfabb0ed96f"

SIGN_INVENTORY = frozenset("acdefghiklmnopqrst y".replace(" ", ""))
PRIMITIVES = frozenset("acehilosy")
_PHYSICAL_FOLIO_RE = re.compile(r"^(f\d+)[rv]\d*$")
_CURRIER_VALUES = frozenset({"A", "B"})
_HAND_VALUES = frozenset({"1", "2", "3", "4", "5"})
_ILLUSTRATION_VALUES = frozenset({"A", "B", "C", "H", "P", "S", "T", "Z"})

FROZEN_FEASIBILITY_INVENTORY: Mapping[str, Mapping[str, Any]] = {
    "overall": {
        "lines": 1_185,
        "physical_folios": 92,
        "by_currier": {"A": 503, "B": 682},
        "by_hand": {"1": 487, "2": 377, "3": 305, "5": 16},
        "by_illustration": {"B": 266, "C": 20, "H": 521, "P": 39, "S": 290, "T": 49},
    },
    "discovery": {
        "lines": 919,
        "physical_folios": 69,
        "by_currier": {"A": 332, "B": 587},
        "by_hand": {"1": 332, "2": 357, "3": 214, "5": 16},
        "by_illustration": {"B": 266, "C": 20, "H": 360, "P": 25, "S": 199, "T": 49},
    },
    "holdout": {
        "lines": 266,
        "physical_folios": 23,
        "by_currier": {"A": 171, "B": 95},
        "by_hand": {"1": 155, "2": 20, "3": 91},
        "by_illustration": {"H": 161, "P": 14, "S": 91},
    },
}

_PAIR_COMPONENTS: Mapping[str, str] = {
    "d": "ey",
    "f": "id",
    "g": "cd",
    "k": "il",
    "m": "id",
    "n": "i",
    "p": "qd",
    "q": "ie",
    "r": "si",
    "t": "ql",
}
_OPTIONAL_E_COMPONENTS: Mapping[str, str] = {
    **_PAIR_COMPONENTS,
    "f": "ide",
    "p": "qde",
}


@dataclass(frozen=True)
class EligibleLine:
    """One exact-consensus line, before any component expansion."""

    page_id: str
    locus_number: int
    physical_folio: str
    currier: str
    hand: str
    illustration: str
    tokens: Sequence[str]

    @property
    def line_id(self) -> str:
        return f"{self.page_id}.{self.locus_number}"

    @property
    def split(self) -> str:
        return "holdout" if is_holdout_physical_folio(self.physical_folio) else "discovery"


@dataclass(frozen=True)
class LineAudit:
    """Fail-closed admission decision that contains no line-length residue."""

    page_id: str
    locus_number: int
    admitted: bool
    reasons: tuple[str, ...]
    physical_folio: str | None
    split: str | None
    zl_brace_notation_present: bool
    it_brace_notation_present: bool

    @property
    def line_id(self) -> str:
        return f"{self.page_id}.{self.locus_number}"


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic JSON bytes for the generated result artifact."""

    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def render_sha256_sidecar(report_sha256: str, json_filename: str) -> str:
    """Render the exact one-line checksum sidecar."""

    if not re.fullmatch(r"[0-9a-f]{64}", report_sha256):
        raise ValueError("report SHA-256 must be 64 lowercase hexadecimal characters")
    if not json_filename or "/" in json_filename or "\\" in json_filename:
        raise ValueError("sidecar requires a basename, not a path")
    return f"{report_sha256}  {json_filename}\n"


def recorded_relative_path(path: Path | str, repository_root: Path | str) -> str:
    """Return a cwd-independent POSIX path relative to the repository root.

    Artifact hashes must not depend on whether the analyzer was launched from
    the repository root or another working directory.  Inputs outside the
    repository remain explicit through ``..`` components rather than falling
    back to the caller's original, potentially relative spelling.
    """

    resolved_path = Path(path).resolve()
    resolved_root = Path(repository_root).resolve()
    return Path(os.path.relpath(resolved_path, resolved_root)).as_posix()


def physical_folio(page_id: str) -> str:
    match = _PHYSICAL_FOLIO_RE.fullmatch(page_id)
    if match is None:
        raise ValueError(f"cannot derive physical folio from {page_id!r}")
    return match.group(1)


def is_holdout_physical_folio(folio_id: str) -> bool:
    if not re.fullmatch(r"f\d+", folio_id):
        raise ValueError(f"invalid physical folio {folio_id!r}")
    return sha256(f"{ANALYSIS_VERSION}:{folio_id}".encode("ascii")).digest()[0] < 51


def _component_table(model_id: str) -> Mapping[str, str]:
    if model_id == "PAIR":
        return _PAIR_COMPONENTS
    if model_id == "OPTIONAL_E":
        return _OPTIONAL_E_COMPONENTS
    raise ValueError(f"unknown H006 component model {model_id!r}")


def expand_sign(sign: str, model_id: str) -> str:
    """Recursively expand one frozen EVA sign into the nine primitives."""

    if len(sign) != 1 or sign not in SIGN_INVENTORY:
        raise ValueError(f"unsupported H006 sign {sign!r}")
    table = _component_table(model_id)

    def visit(value: str, active: frozenset[str]) -> str:
        if value in PRIMITIVES:
            return value
        if value in active:
            raise ValueError(f"cyclic H006 component expansion at {value!r}")
        try:
            components = table[value]
        except KeyError as exc:  # defensive: inventory and table must be total
            raise ValueError(f"no H006 expansion for {value!r}") from exc
        next_active = active | {value}
        return "".join(visit(component, next_active) for component in components)

    expanded = visit(sign, frozenset())
    if not expanded or not set(expanded) <= PRIMITIVES:
        raise AssertionError(f"non-primitive H006 expansion for {sign!r}: {expanded!r}")
    return expanded


def expand_tokens(tokens: Sequence[str], model_id: str) -> str:
    """Expand tokens without adding a word or line boundary symbol."""

    return "".join(expand_sign(sign, model_id) for token in tokens for sign in token)


def primitive_count(tokens: Sequence[str], model_id: str) -> int:
    return sum(len(expand_sign(sign, model_id)) for token in tokens for sign in token)


def _locus_map(document: Document) -> dict[tuple[str, int], list[Locus]]:
    result: dict[tuple[str, int], list[Locus]] = defaultdict(list)
    for locus in document.loci:
        result[(locus.page_id, locus.number)].append(locus)
    return dict(result)


def _known_zl_stratum(locus: Locus) -> tuple[str, str, str] | None:
    currier = locus.effective_variables.get("L")
    hand = locus.effective_variables.get("H")
    illustration = locus.effective_variables.get("I")
    if (
        currier not in _CURRIER_VALUES
        or hand not in _HAND_VALUES
        or illustration not in _ILLUSTRATION_VALUES
    ):
        return None
    return currier, hand, illustration


def _tokenization_reasons(prefix: str, text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    tokenization = tokenize_certain_basic_eva(text)
    labels: set[str] = set()
    for component in tokenization.components:
        source = component.source
        if "," in source:
            labels.add("uncertain_word_space")
        if any(marker in source for marker in ("[", "]", ":")):
            labels.add("alternative_reading")
        if "?" in source:
            labels.add("unreadable_glyph")
        if "@" in source or ";" in source:
            labels.add("extended_eva")
        if re.search(r"[A-Z]", source):
            labels.add("joined_eva_form")
        if "'" in source:
            labels.add("apostrophe")
        if set(source) - set("abcdefghijklmnopqrstuvwxyz',[]:?@;"):
            labels.add("unsupported_symbol")
        if component.exclusion_reason is not None:
            labels.add(component.exclusion_reason)
    reasons = [f"{prefix}_excluded:{label}" for label in sorted(labels)]
    if not tokenization.tokens:
        reasons.append(f"{prefix}_no_certain_token")
    return tokenization.tokens, tuple(reasons)


def _has_brace_notation(text: str) -> bool:
    """Detect IVTFF ligature braces while ignoring inert inline comments."""

    glyph_text = re.sub(r"<[^>]*>", "", text)
    return "{" in glyph_text or "}" in glyph_text


def build_eligible_lines(
    zl: Document, it: Document
) -> tuple[tuple[EligibleLine, ...], tuple[LineAudit, ...]]:
    """Build the exact-consensus inventory without expanding any line."""

    if zl.header.alphabet != "Eva-" or it.header.alphabet != "EvaT":
        raise ValueError("H006 requires ZL alphabet Eva- and IT alphabet EvaT")

    zl_map = _locus_map(zl)
    it_map = _locus_map(it)
    lines: list[EligibleLine] = []
    audits: list[LineAudit] = []
    for page_id, locus_number in sorted(set(zl_map) | set(it_map)):
        reasons: list[str] = []
        zl_candidates = zl_map.get((page_id, locus_number), [])
        it_candidates = it_map.get((page_id, locus_number), [])
        zl_braces = any(_has_brace_notation(locus.text) for locus in zl_candidates)
        it_braces = any(_has_brace_notation(locus.text) for locus in it_candidates)
        if len(zl_candidates) != 1:
            reasons.append("missing_or_duplicate_zl_locus")
        if len(it_candidates) != 1:
            reasons.append("missing_or_duplicate_it_locus")

        try:
            folio = physical_folio(page_id)
        except ValueError:
            folio = None
            reasons.append("invalid_physical_folio")

        zl_locus = zl_candidates[0] if len(zl_candidates) == 1 else None
        it_locus = it_candidates[0] if len(it_candidates) == 1 else None
        stratum: tuple[str, str, str] | None = None
        zl_tokens: tuple[str, ...] = ()
        it_tokens: tuple[str, ...] = ()
        if zl_locus is not None:
            if zl_locus.generic_type != "P":
                reasons.append("nonprose_locus")
            if zl_locus.locator == "!":
                reasons.append("invalid_locator")
            stratum = _known_zl_stratum(zl_locus)
            if stratum is None:
                reasons.append("zl_metadata_outside_frozen_domains")

            zl_tokens, zl_reasons = _tokenization_reasons("zl", zl_locus.text)
            reasons.extend(zl_reasons)

        if it_locus is not None:
            if it_locus.generic_type != "P":
                reasons.append("nonprose_locus")
            if it_locus.locator == "!":
                reasons.append("invalid_locator")
            it_tokens, it_reasons = _tokenization_reasons("it", it_locus.text)
            reasons.extend(it_reasons)

        if zl_locus is not None and it_locus is not None:
            try:
                zl_folio = physical_folio(zl_locus.page_id)
                it_folio = physical_folio(it_locus.page_id)
                if zl_folio != it_folio:
                    reasons.append("nonmatching_physical_folio")
            except ValueError:
                # The key-level invalid_physical_folio reason already records this.
                pass
            if zl_tokens != it_tokens:
                reasons.append("zl_it_token_disagreement")

        available_tokens = (*zl_tokens, *it_tokens)
        if available_tokens:
            unsupported = sorted(set("".join(available_tokens)) - SIGN_INVENTORY)
            if unsupported:
                reasons.append("outside_frozen_sign_inventory")
            if any("n" in token[:-1] for token in available_tokens):
                reasons.append("midword_n")

        unique_reasons = tuple(dict.fromkeys(reasons))
        admitted = not unique_reasons
        split = (
            "holdout" if folio is not None and is_holdout_physical_folio(folio)
            else "discovery" if folio is not None
            else None
        )
        audits.append(
            LineAudit(
                page_id,
                locus_number,
                admitted,
                unique_reasons,
                folio,
                split,
                zl_braces,
                it_braces,
            )
        )
        if admitted:
            assert folio is not None and stratum is not None and zl_tokens
            lines.append(
                EligibleLine(
                    page_id,
                    locus_number,
                    folio,
                    stratum[0],
                    stratum[1],
                    stratum[2],
                    zl_tokens,
                )
            )
    return tuple(lines), tuple(audits)


def _counts_by(lines: Sequence[EligibleLine], attribute: str) -> dict[str, int]:
    return dict(sorted(Counter(str(getattr(line, attribute)) for line in lines).items()))


def inventory_summary(lines: Sequence[EligibleLine]) -> dict[str, Any]:
    """Summarize eligibility/split breadth without reading ``line.tokens``."""

    return {
        "lines": len(lines),
        "physical_folios": len({line.physical_folio for line in lines}),
        "by_currier": _counts_by(lines, "currier"),
        "by_hand": _counts_by(lines, "hand"),
        "by_illustration": _counts_by(lines, "illustration"),
    }


def split_inventory_summary(lines: Sequence[EligibleLine]) -> dict[str, dict[str, Any]]:
    """Return the complete frozen pre-expansion inventory shape."""

    discovery = tuple(line for line in lines if line.split == "discovery")
    holdout = tuple(line for line in lines if line.split == "holdout")
    return {
        "overall": inventory_summary(lines),
        "discovery": inventory_summary(discovery),
        "holdout": inventory_summary(holdout),
    }


def require_frozen_inventory(
    lines: Sequence[EligibleLine],
    expected: Mapping[str, Mapping[str, Any]] = FROZEN_FEASIBILITY_INVENTORY,
) -> dict[str, dict[str, Any]]:
    """Abort before expansion unless every frozen feasibility count matches."""

    observed = split_inventory_summary(lines)
    if observed != expected:
        raise ValueError(
            "H006 frozen feasibility inventory mismatch; no residue was computed: "
            + json.dumps({"expected": expected, "observed": observed}, sort_keys=True)
        )
    return observed


def discovery_breadth_checks(lines: Sequence[EligibleLine]) -> dict[str, bool]:
    inventory = inventory_summary(lines)
    return {
        "at_least_800_lines": inventory["lines"] >= 800,
        "at_least_60_physical_folios": inventory["physical_folios"] >= 60,
        "currier_A_at_least_300_lines": inventory["by_currier"].get("A", 0) >= 300,
        "currier_B_at_least_500_lines": inventory["by_currier"].get("B", 0) >= 500,
        "hand_1_at_least_300_lines": inventory["by_hand"].get("1", 0) >= 300,
        "hand_2_at_least_300_lines": inventory["by_hand"].get("2", 0) >= 300,
        "hand_3_at_least_150_lines": inventory["by_hand"].get("3", 0) >= 150,
    }


def holdout_breadth_checks(lines: Sequence[EligibleLine]) -> dict[str, bool]:
    inventory = inventory_summary(lines)
    illustration_classes_at_least_ten = sum(
        count >= 10 for count in inventory["by_illustration"].values()
    )
    return {
        "at_least_250_lines": inventory["lines"] >= 250,
        "at_least_20_physical_folios": inventory["physical_folios"] >= 20,
        "currier_A_at_least_100_lines": inventory["by_currier"].get("A", 0) >= 100,
        "currier_B_at_least_75_lines": inventory["by_currier"].get("B", 0) >= 75,
        "hand_1_at_least_100_lines": inventory["by_hand"].get("1", 0) >= 100,
        "hand_2_at_least_20_lines": inventory["by_hand"].get("2", 0) >= 20,
        "hand_3_at_least_75_lines": inventory["by_hand"].get("3", 0) >= 75,
        "at_least_3_illustration_classes_with_10_lines": (
            illustration_classes_at_least_ten >= 3
        ),
    }


def _residue_record(counter: Counter[int]) -> dict[str, Any]:
    histogram = {str(residue): counter.get(residue, 0) for residue in range(3)}
    total = sum(histogram.values())
    zero = histogram["0"]
    return {
        "lines": total,
        "histogram": histogram,
        "zero_residue_lines": zero,
        "contradictions": total - zero,
        "zero_residue_fraction": zero / total if total else None,
        "all_zero": total > 0 and zero == total,
    }


def evaluate_component_model(
    lines: Sequence[EligibleLine], model_id: str
) -> dict[str, Any]:
    """Evaluate residues for an explicitly supplied, already-unsealed split."""

    _component_table(model_id)
    overall: Counter[int] = Counter()
    grouped: dict[str, dict[str, Counter[int]]] = {
        dimension: defaultdict(Counter)
        for dimension in ("currier", "hand", "illustration")
    }
    for line in lines:
        residue = primitive_count(line.tokens, model_id) % 3
        overall[residue] += 1
        grouped["currier"][line.currier][residue] += 1
        grouped["hand"][line.hand][residue] += 1
        grouped["illustration"][line.illustration][residue] += 1

    by_dimension = {
        f"by_{dimension}": {
            key: _residue_record(counter)
            for key, counter in sorted(values.items())
        }
        for dimension, values in grouped.items()
    }
    overall_record = _residue_record(overall)
    reported_records = [
        overall_record,
        *(
            record
            for dimension in by_dimension.values()
            for record in dimension.values()
        ),
    ]
    all_reported_subgroups_zero = bool(reported_records) and all(
        record["all_zero"] for record in reported_records
    )
    return {
        "model_id": model_id,
        "overall": overall_record,
        **by_dimension,
        "all_reported_subgroups_zero": all_reported_subgroups_zero,
        "deterministic_residue_gate_met": all_reported_subgroups_zero,
        "p_value_computed": False,
        "null_model_computed": False,
    }


def run_frame_screen(lines: Sequence[EligibleLine]) -> dict[str, Any]:
    """Run discovery and conditionally unseal holdout under the frozen rules."""

    discovery = tuple(line for line in lines if line.split == "discovery")
    holdout = tuple(line for line in lines if line.split == "holdout")
    discovery_inventory = inventory_summary(discovery)
    holdout_inventory = inventory_summary(holdout)
    discovery_breadth = discovery_breadth_checks(discovery)
    holdout_breadth = holdout_breadth_checks(holdout)
    discovery_breadth_met = all(discovery_breadth.values())
    holdout_breadth_met = all(holdout_breadth.values())

    discovery_models: dict[str, Any] = {}
    if discovery_breadth_met:
        discovery_models = {
            model_id: evaluate_component_model(discovery, model_id)
            for model_id in MODEL_IDS
        }
    qualifying = [
        model_id
        for model_id in MODEL_IDS
        if discovery_models.get(model_id, {}).get("deterministic_residue_gate_met", False)
    ]
    locked_model = "PAIR" if "PAIR" in qualifying else qualifying[0] if qualifying else None

    heldout_result: dict[str, Any] = {
        "inventory": holdout_inventory,
        "breadth_checks": holdout_breadth,
        "breadth_gate_met": holdout_breadth_met,
        "residue_evaluated": False,
        "residue_reported": False,
        "sealed": True,
    }
    holdout_gate_met = False
    key_plaintext_stage_authorized = False
    if locked_model is not None and holdout_breadth_met:
        model_result = evaluate_component_model(holdout, locked_model)
        holdout_gate_met = model_result["deterministic_residue_gate_met"]
        key_plaintext_stage_authorized = holdout_gate_met
        heldout_result.update(
            {
                "residue_evaluated": True,
                "residue_reported": True,
                "sealed": False,
                "locked_model_result": model_result,
            }
        )

    if not discovery_breadth_met:
        disposition = (
            "inconclusive: frozen discovery breadth failed; discovery model "
            "dispositions were not computed and held-out residues remain sealed"
        )
    elif locked_model is None:
        disposition = (
            "reject H006-FR3-LINE-v1: neither frozen component model met the "
            "exact discovery line-frame condition; held-out residues remain sealed"
        )
    elif not holdout_breadth_met:
        disposition = (
            "inconclusive: discovery qualified but frozen held-out breadth failed; "
            "held-out residues remain sealed"
        )
    elif holdout_gate_met:
        disposition = (
            "promising line-frame compatibility only; authorize a separately frozen "
            "H006-FR3 key/plaintext stage"
        )
    else:
        disposition = (
            "reject the locked H006-FR3-LINE-v1 component model on an exact "
            "held-out line-frame contradiction"
        )

    return {
        "discovery": {
            "inventory": discovery_inventory,
            "breadth_checks": discovery_breadth,
            "breadth_gate_met": discovery_breadth_met,
            "residue_evaluated": discovery_breadth_met,
            "model_dispositions_computed": discovery_breadth_met,
            "component_models": discovery_models,
            "qualifying_models": qualifying,
            "locked_model": locked_model,
        },
        "holdout": heldout_result,
        "holdout_gate_met": holdout_gate_met,
        "key_plaintext_stage_authorized": key_plaintext_stage_authorized,
        "decoded_string_emitted": False,
        "language_model_used": False,
        "dictionary_used": False,
        "gloss_authorized": False,
        "disposition": disposition,
    }


def build_h006_report(
    protocol_bytes: bytes,
    zl_bytes: bytes,
    it_bytes: bytes,
    *,
    _expected_protocol_sha256: str = PROTOCOL_SHA256,
    _expected_zl_sha256: str = ZL_EVA_SHA256,
    _expected_it_sha256: str = IT_EVA_SHA256,
    _expected_inventory: Mapping[str, Mapping[str, Any]] = FROZEN_FEASIBILITY_INVENTORY,
) -> dict[str, Any]:
    """Validate raw bytes before parsing, then run the guarded frame screen.

    The underscored expected-value injections exist only for synthetic unit
    fixtures.  The production CLI exposes no override and therefore always
    uses the frozen hashes and feasibility inventory.
    """

    observed = {
        "protocol": sha256(protocol_bytes).hexdigest(),
        "zl_eva": sha256(zl_bytes).hexdigest(),
        "it_eva": sha256(it_bytes).hexdigest(),
    }
    expected = {
        "protocol": _expected_protocol_sha256,
        "zl_eva": _expected_zl_sha256,
        "it_eva": _expected_it_sha256,
    }
    for name in ("protocol", "zl_eva", "it_eva"):
        if observed[name] != expected[name]:
            raise ValueError(
                f"unexpected H006 {name} SHA-256: {observed[name]} "
                f"(expected {expected[name]})"
            )

    # Parsing is intentionally after all three raw byte-hash checks.
    zl = parse_ivtff(zl_bytes)
    it = parse_ivtff(it_bytes)
    if zl.header.alphabet != "Eva-":
        raise ValueError(f"unexpected H006 ZL IVTFF alphabet {zl.header.alphabet!r}")
    if it.header.alphabet != "EvaT":
        raise ValueError(f"unexpected H006 IT IVTFF alphabet {it.header.alphabet!r}")
    if zl.emit() != zl_bytes or it.emit() != it_bytes:
        raise ValueError("H006 parsed document did not emit its exact input bytes")

    lines, audits = build_eligible_lines(zl, it)
    frozen_inventory = require_frozen_inventory(lines, _expected_inventory)
    screen = run_frame_screen(lines)
    excluded = [audit for audit in audits if not audit.admitted]
    brace_audit = {
        "zl_keys": sum(audit.zl_brace_notation_present for audit in audits),
        "it_keys": sum(audit.it_brace_notation_present for audit in audits),
        "either_witness_keys": sum(
            audit.zl_brace_notation_present or audit.it_brace_notation_present
            for audit in audits
        ),
        "both_witness_keys": sum(
            audit.zl_brace_notation_present and audit.it_brace_notation_present
            for audit in audits
        ),
        "admitted_either_witness_keys": sum(
            audit.admitted
            and (audit.zl_brace_notation_present or audit.it_brace_notation_present)
            for audit in audits
        ),
        "excluded_either_witness_keys": sum(
            not audit.admitted
            and (audit.zl_brace_notation_present or audit.it_brace_notation_present)
            for audit in audits
        ),
    }
    return {
        "hypothesis_id": "H006-FR3-LINE",
        "analysis_version": ANALYSIS_VERSION,
        "stage": "key-independent fixed-three-trit line-frame screen",
        "claim_scope": (
            "project-instantiated author-mentioned component choices plus fixed "
            "three-trit blocks and independent IVTFF logical-locus resets"
        ),
        "inputs": {
            "protocol": {"sha256": observed["protocol"]},
            "zl_eva": {
                "sha256": observed["zl_eva"],
                "alphabet": zl.header.alphabet,
                "byte_identical_emit_verified": True,
            },
            "it_eva": {
                "sha256": observed["it_eva"],
                "alphabet": it.header.alphabet,
                "byte_identical_emit_verified": True,
            },
        },
        "frozen_rules": {
            "models": list(MODEL_IDS),
            "physical_folio_regex": _PHYSICAL_FOLIO_RE.pattern,
            "holdout_rule": (
                "first_byte(SHA256('H006-FR3-LINE-v1:' + physical_folio_id)) < 51"
            ),
            "advancement": "every eligible line has primitive_count mod 3 == 0",
            "p_values_forbidden": True,
            "error_tolerance": 0,
        },
        "pre_expansion_inventory_guard": {
            "met": True,
            "observed": frozen_inventory,
            "matches_published_frozen_inventory": (
                _expected_inventory is FROZEN_FEASIBILITY_INVENTORY
            ),
        },
        "eligibility": {
            "aligned_keys_audited": len(audits),
            "eligible_lines": len(lines),
            "excluded_keys": len(excluded),
            "brace_notation_audit": brace_audit,
            "exclusion_reason_counts": dict(
                sorted(Counter(reason for audit in excluded for reason in audit.reasons).items())
            ),
            "line_audit": [
                {
                    "line_id": audit.line_id,
                    "admitted": audit.admitted,
                    "reasons": list(audit.reasons),
                    "physical_folio": audit.physical_folio,
                    "split": audit.split,
                    "zl_brace_notation_present": audit.zl_brace_notation_present,
                    "it_brace_notation_present": audit.it_brace_notation_present,
                }
                for audit in audits
            ],
        },
        "screen": screen,
    }


def render_h006_markdown(report: Mapping[str, Any], report_sha256: str) -> str:
    """Render a compact report without inventing fields for sealed residues."""

    screen = report["screen"]
    discovery = screen["discovery"]
    holdout = screen["holdout"]
    eligibility = report["eligibility"]
    brace_audit = eligibility["brace_notation_audit"]
    lines = [
        "# H006-FR3-LINE fixed-three-trit frame screen",
        "",
        f"Machine-readable JSON SHA-256: `{report_sha256}`",
        "",
        f"Disposition: **{screen['disposition']}**",
        "",
        "## Boundary",
        "",
        "This deterministic screen tests line-length divisibility only. It emits no",
        "plaintext, language, word segmentation, dictionary result, or gloss. No iid",
        "null or p-value is part of the frozen protocol.",
        "",
        "## Exact-consensus inventory",
        "",
        f"- Aligned locus keys audited: {report['eligibility']['aligned_keys_audited']}",
        f"- Eligible lines: {report['eligibility']['eligible_lines']}",
        f"- Excluded keys: {report['eligibility']['excluded_keys']}",
        f"- Discovery lines / folios: {discovery['inventory']['lines']} / "
        f"{discovery['inventory']['physical_folios']}",
        f"- Sealed-holdout lines / folios: {holdout['inventory']['lines']} / "
        f"{holdout['inventory']['physical_folios']}",
        "",
        "## Eligibility attrition",
        "",
        "Exclusion counts are multi-label: one key can contribute to every",
        "applicable reason below, but no key enters the eligible inventory twice.",
        "",
        f"- Keys with ZL brace notation: {brace_audit['zl_keys']}",
        f"- Keys with IT brace notation: {brace_audit['it_keys']}",
        "- Admitted keys with brace notation in either witness: "
        f"{brace_audit['admitted_either_witness_keys']}",
        "- Excluded keys with brace notation in either witness: "
        f"{brace_audit['excluded_either_witness_keys']}",
        "",
        "| Exclusion reason | Keys |",
        "| --- | ---: |",
        *[
            f"| `{reason}` | {count} |"
            for reason, count in eligibility["exclusion_reason_counts"].items()
        ],
        "",
        "## Discovery",
        "",
        f"- Breadth gate: {'pass' if discovery['breadth_gate_met'] else 'fail'}",
        f"- Qualifying models: {', '.join(discovery['qualifying_models']) or 'none'}",
        (
            f"- Locked model: `{discovery['locked_model']}`"
            if discovery["locked_model"]
            else "- Locked model: none"
        ),
    ]
    if discovery["residue_evaluated"]:
        lines.extend(
            [
                "",
                "| Model | Residue 0 | Residue 1 | Residue 2 | Contradictions | Exact gate |",
                "| --- | ---: | ---: | ---: | ---: | :---: |",
            ]
        )
        for model_id in MODEL_IDS:
            result = discovery["component_models"][model_id]
            histogram = result["overall"]["histogram"]
            lines.append(
                f"| `{model_id}` | {histogram['0']} | {histogram['1']} | "
                f"{histogram['2']} | {result['overall']['contradictions']} | "
                f"{'pass' if result['deterministic_residue_gate_met'] else 'fail'} |"
            )
    else:
        lines.extend(
            [
                "",
                "Discovery residues and model dispositions were not computed because the",
                "frozen discovery breadth gate failed.",
            ]
        )

    lines.extend(["", "## Held-out stage", ""])
    if not holdout["residue_evaluated"]:
        lines.extend(
            [
                "Held-out residues were not computed or reported and remain sealed.",
                "",
                f"- Holdout breadth gate: {'pass' if holdout['breadth_gate_met'] else 'fail'}",
                "- Key/plaintext stage authorized: false",
            ]
        )
    else:
        result = holdout["locked_model_result"]
        histogram = result["overall"]["histogram"]
        lines.extend(
            [
                f"- Locked model: `{result['model_id']}`",
                f"- Residue histogram: 0={histogram['0']}, 1={histogram['1']}, 2={histogram['2']}",
                f"- Contradictions: {result['overall']['contradictions']}",
                f"- Exact holdout gate: {'pass' if screen['holdout_gate_met'] else 'fail'}",
                "- Key/plaintext stage authorized: "
                f"{str(screen['key_plaintext_stage_authorized']).lower()}",
            ]
        )
    lines.extend(
        [
            "",
            "## Input hashes",
            "",
            *[
                f"- `{name}`: `{item['sha256']}`"
                for name, item in sorted(report["inputs"].items())
            ],
            "",
        ]
    )
    return "\n".join(lines)
