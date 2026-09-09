"""Frozen H007-PK23-COV-v1 published-key coverage screen.

This module deliberately separates three operations:

1. validate and inventory the exact-consensus manuscript corpus without
   opening the Naibbe table;
2. execute the byte-pinned author decoder only on the author's examples; and
3. use the published reverse maps as an opaque six-class observer.

No API in this module returns a plaintext label or a source token.  A failed
discovery screen never passes a held-out token to the table observer.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence

from . import ivtff as ivtff_module
from .ivtff import Document, Locus, parse_ivtff, tokenize_certain_basic_eva


ANALYSIS_VERSION = "H007-PK23-COV-v1"
PROTOCOL_SHA256 = "87dd3743413d8eeed08dd7f9eec4bd05dd25413a14fabb3a473d446a56c01501"
ZL_EVA_SHA256 = "bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc"
IT_EVA_SHA256 = "7f27a8b0feed8f6de0a99900df6bf912dd1d295c38e5f830bac8b41c3f536fb5"
IVTFF_PARSER_SHA256 = "54d915b772d929f3ac5446ec19cbd1c5799956f43cdf5a6bfbb81279da7f693b"
NAIBBE_COMMIT = "f2675ec5dd275268bc64dd48ea64fc0e0e9827a2"

CLASS_IDS = ("U", "B1", "BA", "C1", "CA", "X")
_UNIQUE_CLASSES = frozenset({"U", "B1", "C1"})
_PHYSICAL_FOLIO_RE = re.compile(r"^(f\d+)[rv]\d*$")
_TABLE_CODE_RE = re.compile(
    r"^(unigram|prefix|suffix)_(alpha|beta1|beta2|beta3|gamma1|gamma2)_([a-z])$"
)

VENDOR_FILE_SHA256: Mapping[str, str] = {
    "LICENSE": "e8fb5c1110aaa38618eab2013d1e7c5cae343efd21ea9859478df4930f7746bc",
    "README.md": "b9e78e849a3478341d1c3167b7c3ae960e18f57b4857a0297d296adfe480ec99",
    "decrypt_naibbe.py": "1c18514bbaba914989f1961f41a3930b7c1afe81d6db37b07b1dd7d9e6ea3b49",
    "naibbe.py": "3f5e353d2c50f4e6a6b81567ca31cee4f0537a490b6346d054d26661648a6003",
    "references/naibbe_tables.csv": "4e7cfd54b7ec66515d39a51e11ec97e8e19b643b0b189124eebc3982e707dcec",
    "encrypted/examples/endofpaper.txt": "475055654de0049675c26de7550a37426045e4a57ab533cb97677b390e4764d7",
    "decrypted/examples/endofpaper_decrypted.txt": "c89ca7e66548d76728d968a741296405a271000534f6946d76737fafe7a288c6",
    "encrypted/examples/gallic_naibbe.txt": "c813aa51a843a7c399c4707b000155ba615b00ffe34276054a6e2838cfcc8ae2",
    "decrypted/examples/gallic_decrypted.txt": "c439209d7a3f5492e0adb68505316392ea8b5c25ec7b53605c2d43d27d85ce68",
    "encrypted/nathist_output_ciphertext.txt": "9cdf2de12f371ac7efdb2e78713f229ada508286c1717758184238a59cd64326",
    "decrypted/nathist_output_ciphertext_decrypted.txt": "852d1ad67f82d6472c8ef1d99bfa12c62f76f3d37be2623a131f47232b753ca2",
}

AUTHOR_CONTROLS = (
    (
        "encrypted/examples/endofpaper.txt",
        "decrypted/examples/endofpaper_decrypted.txt",
    ),
    (
        "encrypted/examples/gallic_naibbe.txt",
        "decrypted/examples/gallic_decrypted.txt",
    ),
    (
        "encrypted/nathist_output_ciphertext.txt",
        "decrypted/nathist_output_ciphertext_decrypted.txt",
    ),
)

FROZEN_HOLDOUT_FOLIOS = (
    "f4", "f6", "f7", "f16", "f19", "f22", "f25", "f31", "f33",
    "f35", "f36", "f41", "f42", "f53", "f54", "f66", "f95",
)

FROZEN_CORPUS_INVENTORY: Mapping[str, Any] = {
    "overall": {
        "logical_lines": 526,
        "page_panel_ids": 124,
        "physical_folios": 63,
        "token_occurrences": 3_118,
        "distinct_token_types": 1_261,
        "by_currier": {
            "A": {"lines": 445, "token_occurrences": 2_508},
            "B": {"lines": 80, "token_occurrences": 602},
            "unknown": {"lines": 1, "token_occurrences": 8},
        },
        "by_hand": {
            "1": {"lines": 445, "token_occurrences": 2_508},
            "2": {"lines": 57, "token_occurrences": 418},
            "3": {"lines": 18, "token_occurrences": 141},
            "5": {"lines": 6, "token_occurrences": 51},
        },
    },
    "discovery": {
        "logical_lines": 385,
        "page_panel_ids": 91,
        "physical_folios": 46,
        "token_occurrences": 2_341,
        "distinct_token_types": 1_024,
        "by_currier": {
            "A": {"lines": 329, "token_occurrences": 1_914},
            "B": {"lines": 55, "token_occurrences": 419},
            "unknown": {"lines": 1, "token_occurrences": 8},
        },
        "by_hand": {
            "1": {"lines": 329, "token_occurrences": 1_914},
            "2": {"lines": 48, "token_occurrences": 358},
            "3": {"lines": 5, "token_occurrences": 36},
            "5": {"lines": 3, "token_occurrences": 33},
        },
    },
    "holdout": {
        "logical_lines": 141,
        "page_panel_ids": 33,
        "physical_folios": 17,
        "token_occurrences": 777,
        "distinct_token_types": 451,
        "by_currier": {
            "A": {"lines": 116, "token_occurrences": 594},
            "B": {"lines": 25, "token_occurrences": 183},
        },
        "by_hand": {
            "1": {"lines": 116, "token_occurrences": 594},
            "2": {"lines": 9, "token_occurrences": 60},
            "3": {"lines": 13, "token_occurrences": 105},
            "5": {"lines": 3, "token_occurrences": 18},
        },
    },
    "type_overlap": {
        "shared": 214,
        "discovery_only": 810,
        "holdout_only": 237,
    },
    "holdout_physical_folios": list(FROZEN_HOLDOUT_FOLIOS),
    "apostrophe_bearing_token_occurrences": 0,
}


class H007InputError(ValueError):
    """Raised before a manuscript token can meet the published table."""


class H007Stage0Error(RuntimeError):
    """Raised when the literal author-decoder controls do not reproduce."""


@dataclass(frozen=True)
class EligibleLine:
    """One exact-consensus logical prose locus, before table observation."""

    page_id: str
    locus_number: int
    physical_folio: str
    currier: str
    hand: str
    tokens: Sequence[str]

    @property
    def split(self) -> str:
        return "holdout" if is_holdout_physical_folio(self.physical_folio) else "discovery"


@dataclass(frozen=True)
class LineAudit:
    """Table-independent admission record; never serialized in H007 output."""

    page_id: str
    locus_number: int
    admitted: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class _PublishedMaps:
    unigram: Mapping[str, str]
    prefix: Mapping[str, str]
    suffix: Mapping[str, str]
    all_word_types: frozenset[str]


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def render_sha256_sidecar(report_sha256: str, json_filename: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", report_sha256):
        raise ValueError("report SHA-256 must be 64 lowercase hexadecimal characters")
    if not json_filename or "/" in json_filename or "\\" in json_filename:
        raise ValueError("sidecar requires a basename")
    return f"{report_sha256}  {json_filename}\n"


def recorded_relative_path(path: Path | str, repository_root: Path | str) -> str:
    resolved = Path(path).resolve()
    root = Path(repository_root).resolve()
    return Path(os.path.relpath(resolved, root)).as_posix()


def physical_folio(page_id: str) -> str:
    match = _PHYSICAL_FOLIO_RE.fullmatch(page_id)
    if match is None:
        raise ValueError("page identifier has no frozen physical-folio mapping")
    return match.group(1)


def is_holdout_physical_folio(folio_id: str) -> bool:
    if not re.fullmatch(r"f\d+", folio_id):
        raise ValueError("invalid physical folio")
    payload = f"{ANALYSIS_VERSION}:{folio_id}".encode("ascii")
    return sha256(payload).digest()[0] < 51


def _locus_map(document: Document) -> dict[tuple[str, int], list[Locus]]:
    result: dict[tuple[str, int], list[Locus]] = defaultdict(list)
    for locus in document.loci:
        result[(locus.page_id, locus.number)].append(locus)
    return dict(result)


def _tokenize_complete(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    tokenization = tokenize_certain_basic_eva(text)
    reasons = tuple(sorted({item.reason for item in tokenization.excluded}))
    if not tokenization.tokens:
        reasons = (*reasons, "no_certain_token")
    return tokenization.tokens, reasons


def validate_corpus_inputs(
    protocol_bytes: bytes,
    zl_bytes: bytes,
    it_bytes: bytes,
    parser_bytes: bytes,
) -> tuple[Document, Document]:
    """Verify all pre-table corpus pins, headers, parses, and round trips."""

    checks = {
        "protocol": (_digest(protocol_bytes), PROTOCOL_SHA256),
        "ZL3b": (_digest(zl_bytes), ZL_EVA_SHA256),
        "IT2a": (_digest(it_bytes), IT_EVA_SHA256),
        "IVTFF parser": (_digest(parser_bytes), IVTFF_PARSER_SHA256),
    }
    mismatches = [name for name, (seen, expected) in checks.items() if seen != expected]
    if mismatches:
        raise H007InputError(
            "H007 pinned input hash mismatch before table load: " + ", ".join(mismatches)
        )

    zl = parse_ivtff(zl_bytes)
    it = parse_ivtff(it_bytes)
    if zl.header.alphabet != "Eva-" or it.header.alphabet != "EvaT":
        raise H007InputError("H007 requires ZL alphabet Eva- and IT alphabet EvaT")
    if zl.emit() != zl_bytes or it.emit() != it_bytes:
        raise H007InputError("H007 IVTFF byte round trip failed before table load")
    return zl, it


def build_eligible_lines(
    zl: Document, it: Document
) -> tuple[tuple[EligibleLine, ...], tuple[LineAudit, ...]]:
    """Build the full exact-consensus inventory without loading Naibbe data."""

    if zl.header.alphabet != "Eva-" or it.header.alphabet != "EvaT":
        raise H007InputError("H007 requires ZL alphabet Eva- and IT alphabet EvaT")

    zl_map = _locus_map(zl)
    it_map = _locus_map(it)
    admitted: list[EligibleLine] = []
    audits: list[LineAudit] = []
    for page_id, locus_number in sorted(set(zl_map) | set(it_map)):
        reasons: list[str] = []
        zl_candidates = zl_map.get((page_id, locus_number), [])
        it_candidates = it_map.get((page_id, locus_number), [])
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
        zl_tokens: tuple[str, ...] = ()
        it_tokens: tuple[str, ...] = ()
        if zl_locus is not None:
            if zl_locus.generic_type != "P":
                reasons.append("zl_nonprose_locus")
            if zl_locus.locator == "!":
                reasons.append("zl_invalid_locator")
            if zl_locus.effective_variables.get("I") != "H":
                reasons.append("zl_not_herbal")
            zl_tokens, token_reasons = _tokenize_complete(zl_locus.text)
            reasons.extend(f"zl_excluded:{reason}" for reason in token_reasons)
        if it_locus is not None:
            if it_locus.generic_type != "P":
                reasons.append("it_nonprose_locus")
            if it_locus.locator == "!":
                reasons.append("it_invalid_locator")
            it_tokens, token_reasons = _tokenize_complete(it_locus.text)
            reasons.extend(f"it_excluded:{reason}" for reason in token_reasons)
        if zl_locus is not None and it_locus is not None and zl_tokens != it_tokens:
            reasons.append("zl_it_token_disagreement")

        unique_reasons = tuple(dict.fromkeys(reasons))
        audits.append(LineAudit(page_id, locus_number, not unique_reasons, unique_reasons))
        if not unique_reasons:
            assert zl_locus is not None and folio is not None and zl_tokens
            admitted.append(
                EligibleLine(
                    page_id=page_id,
                    locus_number=locus_number,
                    physical_folio=folio,
                    currier=zl_locus.effective_variables.get("L", "unknown"),
                    hand=zl_locus.effective_variables.get("H", "unknown"),
                    tokens=zl_tokens,
                )
            )
    return tuple(admitted), tuple(audits)


def _scope_inventory(lines: Sequence[EligibleLine]) -> dict[str, Any]:
    line_currier = Counter(line.currier for line in lines)
    token_currier: Counter[str] = Counter()
    line_hand = Counter(line.hand for line in lines)
    token_hand: Counter[str] = Counter()
    token_types: set[str] = set()
    token_occurrences = 0
    for line in lines:
        count = len(line.tokens)
        token_occurrences += count
        token_types.update(line.tokens)
        token_currier[line.currier] += count
        token_hand[line.hand] += count
    return {
        "logical_lines": len(lines),
        "page_panel_ids": len({line.page_id for line in lines}),
        "physical_folios": len({line.physical_folio for line in lines}),
        "token_occurrences": token_occurrences,
        "distinct_token_types": len(token_types),
        "by_currier": {
            key: {"lines": line_currier[key], "token_occurrences": token_currier[key]}
            for key in sorted(line_currier)
        },
        "by_hand": {
            key: {"lines": line_hand[key], "token_occurrences": token_hand[key]}
            for key in sorted(line_hand)
        },
    }


def corpus_inventory(lines: Sequence[EligibleLine]) -> dict[str, Any]:
    """Return the complete table-independent frozen inventory."""

    discovery = tuple(line for line in lines if line.split == "discovery")
    holdout = tuple(line for line in lines if line.split == "holdout")
    discovery_types = {token for line in discovery for token in line.tokens}
    holdout_types = {token for line in holdout for token in line.tokens}
    holdout_folios = sorted(
        {line.physical_folio for line in holdout}, key=lambda value: int(value[1:])
    )
    return {
        "overall": _scope_inventory(lines),
        "discovery": _scope_inventory(discovery),
        "holdout": _scope_inventory(holdout),
        "type_overlap": {
            "shared": len(discovery_types & holdout_types),
            "discovery_only": len(discovery_types - holdout_types),
            "holdout_only": len(holdout_types - discovery_types),
        },
        "holdout_physical_folios": holdout_folios,
        "apostrophe_bearing_token_occurrences": sum(
            "'" in token for line in lines for token in line.tokens
        ),
    }


def require_frozen_corpus_inventory(
    lines: Sequence[EligibleLine],
    expected: Mapping[str, Any] = FROZEN_CORPUS_INVENTORY,
) -> dict[str, Any]:
    observed = corpus_inventory(lines)
    if observed != expected:
        raise H007InputError(
            "H007 table-independent inventory mismatch; table was not loaded: "
            + json.dumps({"expected": expected, "observed": observed}, sort_keys=True)
        )
    return observed


def verify_vendor_hashes(vendor_root: Path | str) -> dict[str, str]:
    """Verify every pinned upstream byte before running the author decoder."""

    root = Path(vendor_root)
    seen: dict[str, str] = {}
    failures: list[str] = []
    for relative, expected in VENDOR_FILE_SHA256.items():
        path = root / relative
        if not path.is_file():
            failures.append(relative)
            continue
        digest = _digest(path.read_bytes())
        seen[relative] = digest
        if digest != expected:
            failures.append(relative)
    if failures:
        raise H007Stage0Error("H007 pinned author-file verification failed: " + ", ".join(failures))
    return seen


def _vendor_tree_snapshot(vendor_root: Path) -> tuple[tuple[str, str], ...]:
    """Record every upstream file path and byte hash, including unlisted files."""

    return tuple(
        sorted(
            (
                path.relative_to(vendor_root).as_posix(),
                _digest(path.read_bytes()),
            )
            for path in vendor_root.rglob("*")
            if path.is_file()
        )
    )


def _probe_pandas_python(path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    program = (
        "import json,platform,pandas; "
        "print(json.dumps({'python_version':platform.python_version(),"
        "'pandas_version':pandas.__version__},sort_keys=True))"
    )
    try:
        completed = subprocess.run(
            [str(path), "-B", "-I", "-c", program],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        metadata = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None
    if set(metadata) != {"python_version", "pandas_version"}:
        return None
    return {key: str(value) for key, value in metadata.items()}


def locate_pandas_python(explicit: Path | str | None = None) -> tuple[Path, dict[str, str]]:
    """Locate a dependency interpreter; this is not a decoder parameter."""

    candidates: list[tuple[str, Path]] = [("current", Path(sys.executable))]
    env_path = os.environ.get("H007_PANDAS_PYTHON")
    if env_path:
        candidates.append(("environment", Path(env_path)))
    if explicit is not None:
        candidates.append(("explicit", Path(explicit)))

    seen: set[Path] = set()
    for source, candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        metadata = _probe_pandas_python(resolved)
        if metadata is not None:
            return resolved, {**metadata, "interpreter_source": source}
    raise H007Stage0Error("no pandas-capable Python interpreter found for pinned author controls")


_STAGE0_DRIVER = r"""
import importlib.util
import json
import pathlib
import platform
import sys

import pandas

decoder_path, table_path, input_path, output_path = map(pathlib.Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location("h007_pinned_author_decoder", decoder_path)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import pinned decoder")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if module.BASIC is not True or module.MARK_COMPOUND is not True:
    raise RuntimeError("pinned decoder flags differ from frozen protocol")
module.decrypt_naibbe_file(
    input_path=str(input_path),
    output_path=str(output_path),
    glyph_table_path=str(table_path),
    basic=True,
)
print(json.dumps({
    "python_version": platform.python_version(),
    "pandas_version": pandas.__version__,
    "basic": module.BASIC,
    "mark_compound": module.MARK_COMPOUND,
}, sort_keys=True))
"""


def run_stage0_author_controls(
    vendor_root: Path | str,
    pandas_python: Path | str | None = None,
) -> dict[str, Any]:
    """Run the unmodified author decoder on author fixtures only."""

    root = Path(vendor_root).resolve()
    tree_before = _vendor_tree_snapshot(root)
    verify_vendor_hashes(root)
    interpreter, probe = locate_pandas_python(pandas_python)
    observed_environment: dict[str, Any] | None = None
    passed = 0
    with tempfile.TemporaryDirectory(prefix="h007-stage0-") as temp_name:
        temp = Path(temp_name)
        for index, (cipher_rel, plain_rel) in enumerate(AUTHOR_CONTROLS):
            output_path = temp / f"control-{index}.txt"
            try:
                completed = subprocess.run(
                    [
                        str(interpreter), "-B", "-I", "-c", _STAGE0_DRIVER,
                        str(root / "decrypt_naibbe.py"),
                        str(root / "references/naibbe_tables.csv"),
                        str(root / cipher_rel),
                        str(output_path),
                    ],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                environment = json.loads(completed.stdout)
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
                raise H007Stage0Error("pinned author decoder control execution failed") from exc
            if environment.get("basic") is not True or environment.get("mark_compound") is not True:
                raise H007Stage0Error("pinned author decoder flags failed at runtime")
            if (
                environment.get("python_version") != probe["python_version"]
                or environment.get("pandas_version") != probe["pandas_version"]
            ):
                raise H007Stage0Error("dependency environment changed during Stage 0")
            if observed_environment is None:
                observed_environment = environment
            elif environment != observed_environment:
                raise H007Stage0Error("Stage 0 environment changed between controls")
            if not output_path.is_file() or output_path.read_bytes() != (root / plain_rel).read_bytes():
                raise H007Stage0Error("pinned author decoder output byte comparison failed")
            passed += 1

    # Importing the pinned module is allowed to read, but never mutate, raw data.
    # The complete path+hash snapshot also catches an unexpected new file.
    if _vendor_tree_snapshot(root) != tree_before:
        raise H007Stage0Error("pinned author tree changed during Stage 0")
    verify_vendor_hashes(root)

    return {
        "passed": passed == len(AUTHOR_CONTROLS),
        "controls_run": len(AUTHOR_CONTROLS),
        "controls_passed": passed,
        "settings": {"basic": True, "mark_compound": True},
        "environment": {
            "python_version": probe["python_version"],
            "pandas_version": probe["pandas_version"],
        },
        "comparison": "exact_utf8_output_bytes",
    }


def _load_published_maps(table_bytes: bytes) -> tuple[_PublishedMaps, dict[str, int]]:
    """Load the pinned CSV after inventory and Stage 0; labels stay internal."""

    if _digest(table_bytes) != VENDOR_FILE_SHA256["references/naibbe_tables.csv"]:
        raise H007Stage0Error("published table hash changed after Stage 0")
    reader = csv.DictReader(io.StringIO(table_bytes.decode("utf-8-sig"), newline=""))
    if reader.fieldnames != ["code", "glyphs"]:
        raise H007Stage0Error("published table header mismatch")
    rows = list(reader)
    unigram: dict[str, str] = {}
    prefix: dict[str, str] = {}
    suffix: dict[str, str] = {}
    all_word_types: set[str] = set()
    labels: set[str] = set()
    tables: set[str] = set()
    role_counts: Counter[str] = Counter()
    codes: set[str] = set()
    for row in rows:
        code = row.get("code") or ""
        glyph = row.get("glyphs") or ""
        match = _TABLE_CODE_RE.fullmatch(code)
        if match is None or not glyph or code in codes:
            raise H007Stage0Error("published table geometry mismatch")
        role, table, label = match.groups()
        codes.add(code)
        labels.add(label)
        tables.add(table)
        role_counts[role] += 1
        all_word_types.add(glyph)
        target = {"unigram": unigram, "prefix": prefix, "suffix": suffix}[role]
        target[glyph] = label

    geometry = {
        "role_entries": len(rows),
        "unigram_entries": role_counts["unigram"],
        "prefix_entries": role_counts["prefix"],
        "suffix_entries": role_counts["suffix"],
        "tables": len(tables),
        "opaque_plaintext_labels": len(labels),
        "distinct_ciphertext_strings": len(all_word_types),
    }
    expected_geometry = {
        "role_entries": 414,
        "unigram_entries": 138,
        "prefix_entries": 138,
        "suffix_entries": 138,
        "tables": 6,
        "opaque_plaintext_labels": 23,
        "distinct_ciphertext_strings": 356,
    }
    if geometry != expected_geometry:
        raise H007Stage0Error("published table geometry mismatch")
    return _PublishedMaps(unigram, prefix, suffix, frozenset(all_word_types)), geometry


class PublishedClassObserver:
    """Opaque observer for the author's BASIC/compound reverse control flow."""

    def __init__(
        self,
        unigram: Mapping[str, str],
        prefix: Mapping[str, str],
        suffix: Mapping[str, str],
        all_word_types: Iterable[str],
    ) -> None:
        self._maps = _PublishedMaps(
            dict(unigram), dict(prefix), dict(suffix), frozenset(all_word_types)
        )

    @classmethod
    def from_pinned_table(cls, table_bytes: bytes) -> tuple["PublishedClassObserver", dict[str, int]]:
        maps, geometry = _load_published_maps(table_bytes)
        return cls(maps.unigram, maps.prefix, maps.suffix, maps.all_word_types), geometry

    def _direct_class(self, token: str) -> str:
        if token in self._maps.unigram:
            return "U"
        candidates: list[tuple[str, str]] = []
        for index in range(1, len(token)):
            left = token[:index]
            right = token[index:]
            if left in self._maps.prefix and right in self._maps.suffix:
                candidate = (self._maps.prefix[left], self._maps.suffix[right])
                if candidate not in candidates:
                    candidates.append(candidate)
        if len(candidates) == 1:
            return "B1"
        if len(candidates) > 1:
            return "BA"
        return "X"

    def classify(self, token: str) -> str:
        direct = self._direct_class(token)
        if direct != "X":
            return direct

        viable: list[tuple[str, str]] = []
        for index in range(1, len(token)):
            left = token[:index]
            right = token[index:]
            if left not in self._maps.all_word_types or right not in self._maps.all_word_types:
                continue
            left_class = self._direct_class(left)
            right_class = self._direct_class(right)
            if left_class != "X" and right_class != "X":
                viable.append((left_class, right_class))
        if not viable:
            return "X"
        if len(viable) == 1 and all(item in _UNIQUE_CLASSES for item in viable[0]):
            return "C1"
        return "CA"


def _class_histogram(
    lines: Sequence[EligibleLine], observer: PublishedClassObserver
) -> dict[str, Any]:
    occurrence_counts: Counter[str] = Counter()
    type_classes: dict[str, str] = {}
    ordered = sorted(lines, key=lambda line: (line.page_id, line.locus_number))
    for line in ordered:
        for token_index, token in enumerate(line.tokens):
            del token_index  # ordering is intentional; the index is never serialized
            class_id = observer.classify(token)
            if class_id not in CLASS_IDS:
                raise AssertionError("observer returned an unknown H007 class")
            previous = type_classes.setdefault(token, class_id)
            if previous != class_id:
                raise AssertionError("deterministic observer changed class for one type")
            occurrence_counts[class_id] += 1
    type_counts = Counter(type_classes.values())
    total = sum(occurrence_counts.values())
    histogram = {
        class_id: {
            "occurrences": occurrence_counts[class_id],
            "distinct_types": type_counts[class_id],
        }
        for class_id in CLASS_IDS
    }
    return {
        "evaluated": True,
        "token_occurrences": total,
        "distinct_token_types": len(type_classes),
        "histogram": histogram,
        "generator_membership_gate_met": total > 0 and occurrence_counts["X"] == 0,
        "unique_output_gate_met": (
            total > 0
            and occurrence_counts["X"] == 0
            and occurrence_counts["BA"] == 0
            and occurrence_counts["CA"] == 0
        ),
    }


def run_coverage_screen(
    lines: Sequence[EligibleLine],
    observer: PublishedClassObserver,
    frozen_inventory: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify discovery completely and conditionally unseal held-out types."""

    discovery = tuple(line for line in lines if line.split == "discovery")
    holdout = tuple(line for line in lines if line.split == "holdout")
    discovery_result = _class_histogram(discovery, observer)
    discovery_passed = (
        discovery_result["generator_membership_gate_met"]
        and discovery_result["unique_output_gate_met"]
    )
    holdout_result: dict[str, Any] = {
        "evaluated": False,
        "sealed": True,
        "aggregate_histogram_reported": False,
    }
    separate_output_protocol_authorized = False
    if discovery_passed:
        if frozen_inventory is not None:
            # Recheck the full sealed inventory immediately before the first
            # held-out observer call.  This operation is table-independent.
            require_frozen_corpus_inventory(lines, frozen_inventory)
        holdout_result = _class_histogram(holdout, observer)
        holdout_result["sealed"] = False
        holdout_result["aggregate_histogram_reported"] = True
        separate_output_protocol_authorized = (
            holdout_result["generator_membership_gate_met"]
            and holdout_result["unique_output_gate_met"]
        )

    if not discovery_passed:
        disposition = "rejected_on_discovery"
    elif not separate_output_protocol_authorized:
        disposition = "rejected_on_holdout"
    else:
        disposition = "promising_fixed_table_coverage_and_uniqueness_only"
    return {
        "discovery": discovery_result,
        "discovery_gate_met": discovery_passed,
        "holdout": holdout_result,
        "separate_output_protocol_authorized": separate_output_protocol_authorized,
        "decoded_output_released": False,
        "disposition": disposition,
    }


def _sealed_coverage(disposition: str) -> dict[str, Any]:
    """Return a reportable abort state with no fabricated class histogram."""

    return {
        "discovery": {"evaluated": False},
        "discovery_gate_met": False,
        "holdout": {
            "evaluated": False,
            "sealed": True,
            "aggregate_histogram_reported": False,
        },
        "separate_output_protocol_authorized": False,
        "decoded_output_released": False,
        "disposition": disposition,
    }


def _assemble_h007_report(
    inputs: Mapping[str, Any],
    inventory: Mapping[str, Any],
    stage0: Mapping[str, Any],
    table_geometry: Mapping[str, int] | None,
    coverage: Mapping[str, Any],
) -> dict[str, Any]:
    """Assemble the exact aggregate-only public schema."""

    report = {
        "analysis_version": ANALYSIS_VERSION,
        "claim_scope": "direct_published_fixed_key_coverage_and_uniqueness",
        "inputs": dict(inputs),
        "settings": {
            "basic": True,
            "mark_compound": True,
            "key_search": False,
            "table_completion": False,
            "manual_exceptions": False,
        },
        "table_independent_inventory": dict(inventory),
        "stage0_author_controls": dict(stage0),
        "published_table_integrity": (
            None if table_geometry is None else dict(table_geometry)
        ),
        "coverage": dict(coverage),
        "disposition": coverage["disposition"],
    }
    expected_top_level = {
        "analysis_version",
        "claim_scope",
        "inputs",
        "settings",
        "table_independent_inventory",
        "stage0_author_controls",
        "published_table_integrity",
        "coverage",
        "disposition",
    }
    if set(report) != expected_top_level:
        raise AssertionError("H007 public report schema changed")
    for node in _walk_json(report):
        if isinstance(node, Mapping):
            forbidden = {
                "token_string",
                "token_hash",
                "decoded_letter",
                "decoded_word",
                "decoded_line",
                "candidate_labels",
                "candidate_count",
                "locus_outcomes",
                "folio_outcomes",
            }
            if forbidden & set(node):
                raise AssertionError("H007 public report contains a forbidden field")
    return report


def _walk_json(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def build_h007_report(
    protocol_path: Path | str,
    zl_path: Path | str,
    it_path: Path | str,
    vendor_root: Path | str,
    repository_root: Path | str,
    pandas_python: Path | str | None = None,
) -> dict[str, Any]:
    """Run H007 in the only authorized order and build a leakage-safe report."""

    protocol_path = Path(protocol_path)
    zl_path = Path(zl_path)
    it_path = Path(it_path)
    vendor_root = Path(vendor_root)
    repository_root = Path(repository_root)
    parser_path = Path(ivtff_module.__file__)

    zl, it = validate_corpus_inputs(
        protocol_path.read_bytes(),
        zl_path.read_bytes(),
        it_path.read_bytes(),
        parser_path.read_bytes(),
    )
    lines, _audits = build_eligible_lines(zl, it)
    inventory = require_frozen_corpus_inventory(lines)

    inputs: dict[str, Any] = {
        "protocol": {
            "path": recorded_relative_path(protocol_path, repository_root),
            "sha256": PROTOCOL_SHA256,
        },
        "zl_eva": {
            "path": recorded_relative_path(zl_path, repository_root),
            "sha256": ZL_EVA_SHA256,
            "alphabet": "Eva-",
            "byte_round_trip": True,
        },
        "it_eva": {
            "path": recorded_relative_path(it_path, repository_root),
            "sha256": IT_EVA_SHA256,
            "alphabet": "EvaT",
            "byte_round_trip": True,
            "independent_sample": False,
        },
        "ivtff_parser": {
            "path": recorded_relative_path(parser_path, repository_root),
            "sha256": IVTFF_PARSER_SHA256,
        },
        "naibbe_commit": NAIBBE_COMMIT,
        "naibbe_files": {
            relative: {
                "path": recorded_relative_path(vendor_root / relative, repository_root),
                "sha256": expected,
            }
            for relative, expected in sorted(VENDOR_FILE_SHA256.items())
        },
    }

    # The author controls are deliberately after the complete corpus inventory.
    try:
        stage0 = run_stage0_author_controls(vendor_root, pandas_python)
    except H007Stage0Error:
        stage0 = {
            "passed": False,
            "failure_code": "stage0_failed",
            "settings": {"basic": True, "mark_compound": True},
        }
        return _assemble_h007_report(
            inputs,
            inventory,
            stage0,
            None,
            _sealed_coverage("inconclusive_stage0"),
        )
    if not stage0["passed"]:
        raise AssertionError("Stage 0 returned a non-passing result without raising")

    # This is the first published-table load available to manuscript analysis.
    table_path = vendor_root / "references/naibbe_tables.csv"
    observer, table_geometry = PublishedClassObserver.from_pinned_table(table_path.read_bytes())
    coverage = run_coverage_screen(lines, observer, FROZEN_CORPUS_INVENTORY)
    return _assemble_h007_report(inputs, inventory, stage0, table_geometry, coverage)


def render_h007_markdown(report: Mapping[str, Any], report_sha256: str) -> str:
    coverage = report["coverage"]
    discovery = coverage["discovery"]
    lines = [
        "# H007-PK23-COV published-key coverage screen",
        "",
        f"- Protocol: `{report['analysis_version']}`",
        f"- Disposition: **{report['disposition']}**",
        f"- Stage 0 author controls: **{'pass' if report['stage0_author_controls']['passed'] else 'fail'}**",
        f"- Report SHA-256: `{report_sha256}`",
        "",
        "## Table-independent corpus inventory",
        "",
        "| Scope | Lines | Pages/panels | Physical folios | Occurrences | Distinct types |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    inventory = report["table_independent_inventory"]
    for scope in ("overall", "discovery", "holdout"):
        row = inventory[scope]
        lines.append(
            f"| {scope} | {row['logical_lines']} | {row['page_panel_ids']} | "
            f"{row['physical_folios']} | {row['token_occurrences']} | "
            f"{row['distinct_token_types']} |"
        )
    lines.extend(
        [
            "",
            "The inventory was reproduced before the published table was loaded.",
            "",
            "## Discovery aggregate classes",
            "",
            "| Class | Occurrences | Distinct types |",
            "|---|---:|---:|",
        ]
    )
    if discovery["evaluated"]:
        for class_id in CLASS_IDS:
            row = discovery["histogram"][class_id]
            lines.append(f"| {class_id} | {row['occurrences']} | {row['distinct_types']} |")
        lines.extend(
            [
                "",
                f"Generator-membership gate: **{'pass' if discovery['generator_membership_gate_met'] else 'fail'}**.",
                f"Unique-output gate: **{'pass' if discovery['unique_output_gate_met'] else 'fail'}**.",
                "",
            ]
        )
    else:
        lines.extend(["| not evaluated | - | - |", ""])
    holdout = coverage["holdout"]
    if holdout["evaluated"]:
        lines.extend(
            [
                "## Holdout aggregate classes",
                "",
                "| Class | Occurrences | Distinct types |",
                "|---|---:|---:|",
            ]
        )
        for class_id in CLASS_IDS:
            row = holdout["histogram"][class_id]
            lines.append(f"| {class_id} | {row['occurrences']} | {row['distinct_types']} |")
        lines.append("")
    else:
        if discovery["evaluated"]:
            sealed_reason = (
                "The published table did not evaluate any held-out occurrence "
                "because the discovery gates failed."
            )
        else:
            sealed_reason = (
                "Held-out table evaluation did not begin because the author-control "
                "stage did not pass."
            )
        lines.extend(
            [
                "## Sealed holdout",
                "",
                sealed_reason,
                "",
            ]
        )
    lines.extend(
        [
            "No decoded label, candidate, word, line, or character stream is present in this artifact.",
            "This necessary-condition screen used no stochastic null or semantic scoring.",
            "",
        ]
    )
    return "\n".join(lines)
