from __future__ import annotations

from collections import Counter
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich import ivtff
from voynich.ivtff import parse_ivtff
from voynich.naibbe_coverage import (
    ANALYSIS_VERSION,
    AUTHOR_CONTROLS,
    CLASS_IDS,
    FROZEN_CORPUS_INVENTORY,
    FROZEN_HOLDOUT_FOLIOS,
    IT_EVA_SHA256,
    IVTFF_PARSER_SHA256,
    PROTOCOL_SHA256,
    VENDOR_FILE_SHA256,
    ZL_EVA_SHA256,
    EligibleLine,
    H007InputError,
    H007Stage0Error,
    PublishedClassObserver,
    _assemble_h007_report,
    _load_published_maps,
    _sealed_coverage,
    build_eligible_lines,
    build_h007_report,
    canonical_json_bytes,
    corpus_inventory,
    is_holdout_physical_folio,
    physical_folio,
    render_h007_markdown,
    render_sha256_sidecar,
    require_frozen_corpus_inventory,
    run_coverage_screen,
    run_stage0_author_controls,
    validate_corpus_inputs,
)


PROTOCOL = ROOT / "notes/hypotheses/H007-PK23-published-key-coverage.md"
ZL = ROOT / "data/raw/transcriptions/ZL3b-n.txt"
IT = ROOT / "data/raw/transcriptions/IT2a-n.txt"
VENDOR = ROOT / "data/raw/external/naibbe-f2675ec"
TABLE = VENDOR / "references/naibbe_tables.csv"


def _document(
    records: list[tuple[int, str, str]],
    *,
    alphabet: str = "Eva-",
    metadata: str = "$I=H $L=A $H=1",
) -> object:
    lines = [f"#=IVTFF {alphabet} 2.0 M", f"<f1r> <! {metadata}>"]
    lines.extend(
        f"<f1r.{number},{locator_type}> {text}"
        for number, locator_type, text in records
    )
    return parse_ivtff(("\n".join(lines) + "\n").encode("ascii"))


def _line(folio: str, tokens: tuple[str, ...], number: int = 1) -> EligibleLine:
    return EligibleLine(f"{folio}r", number, folio, "A", "1", tokens)


class H007PinnedCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.zl, cls.it = validate_corpus_inputs(
            PROTOCOL.read_bytes(),
            ZL.read_bytes(),
            IT.read_bytes(),
            Path(ivtff.__file__).read_bytes(),
        )
        cls.lines, cls.audits = build_eligible_lines(cls.zl, cls.it)

    def test_all_pre_table_hash_header_and_round_trip_pins(self) -> None:
        self.assertEqual(sha256(PROTOCOL.read_bytes()).hexdigest(), PROTOCOL_SHA256)
        self.assertEqual(sha256(ZL.read_bytes()).hexdigest(), ZL_EVA_SHA256)
        self.assertEqual(sha256(IT.read_bytes()).hexdigest(), IT_EVA_SHA256)
        self.assertEqual(
            sha256(Path(ivtff.__file__).read_bytes()).hexdigest(),
            IVTFF_PARSER_SHA256,
        )
        self.assertEqual(self.zl.header.alphabet, "Eva-")
        self.assertEqual(self.it.header.alphabet, "EvaT")
        self.assertEqual(self.zl.emit(), ZL.read_bytes())
        self.assertEqual(self.it.emit(), IT.read_bytes())

    def test_hash_failure_aborts_before_parse_or_table(self) -> None:
        with patch("voynich.naibbe_coverage.parse_ivtff") as parser:
            with self.assertRaisesRegex(H007InputError, "hash mismatch before table load"):
                validate_corpus_inputs(
                    PROTOCOL.read_bytes() + b"x",
                    ZL.read_bytes(),
                    IT.read_bytes(),
                    Path(ivtff.__file__).read_bytes(),
                )
            parser.assert_not_called()

    def test_complete_frozen_inventory_matches_every_dimension(self) -> None:
        observed = corpus_inventory(self.lines)
        self.assertEqual(observed, FROZEN_CORPUS_INVENTORY)
        self.assertEqual(require_frozen_corpus_inventory(self.lines), observed)
        self.assertEqual(tuple(observed["holdout_physical_folios"]), FROZEN_HOLDOUT_FOLIOS)
        self.assertEqual(observed["type_overlap"], {
            "shared": 214,
            "discovery_only": 810,
            "holdout_only": 237,
        })
        self.assertEqual(observed["apostrophe_bearing_token_occurrences"], 0)

    def test_inventory_mismatch_fails_before_any_observer_exists(self) -> None:
        with self.assertRaisesRegex(H007InputError, "table was not loaded"):
            require_frozen_corpus_inventory(self.lines[:-1])

    def test_exact_consensus_gate_keeps_apostrophe_and_unknown_currier(self) -> None:
        zl = _document(
            [
                (1, "@P0", "da'in.ol"),
                (2, "@P0", "daiin"),
                (3, "@P0", "daiin,ol"),
                (4, "!P0", "daiin"),
                (5, "@Lf", "daiin"),
            ],
            metadata="$I=H $H=1",
        )
        it = _document(
            [
                (1, "@P0", "da'in.ol"),
                (2, "@P0", "dain"),
                (3, "@P0", "daiin,ol"),
                (4, "@P0", "daiin"),
                (5, "@Lf", "daiin"),
            ],
            alphabet="EvaT",
            metadata="$I=H $H=1",
        )
        lines, audits = build_eligible_lines(zl, it)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].tokens, ("da'in", "ol"))
        self.assertEqual(lines[0].currier, "unknown")
        by_number = {audit.locus_number: audit for audit in audits}
        self.assertIn("zl_it_token_disagreement", by_number[2].reasons)
        self.assertIn("zl_excluded:uncertain_word_space", by_number[3].reasons)
        self.assertIn("zl_invalid_locator", by_number[4].reasons)
        self.assertIn("zl_nonprose_locus", by_number[5].reasons)

    def test_physical_folio_hash_split_is_exact(self) -> None:
        self.assertEqual(physical_folio("f90r2"), "f90")
        self.assertEqual(physical_folio("f90v1"), "f90")
        with self.assertRaises(ValueError):
            physical_folio("fRos")
        expected = sha256(f"{ANALYSIS_VERSION}:f90".encode("ascii")).digest()[0] < 51
        self.assertEqual(is_holdout_physical_folio("f90"), expected)
        self.assertFalse(is_holdout_physical_folio("f1"))
        self.assertTrue(is_holdout_physical_folio("f4"))


class H007Stage0Tests(unittest.TestCase):
    def test_every_vendored_author_byte_is_pinned(self) -> None:
        self.assertEqual(
            {relative: sha256((VENDOR / relative).read_bytes()).hexdigest()
             for relative in VENDOR_FILE_SHA256},
            dict(VENDOR_FILE_SHA256),
        )

    def test_literal_author_controls_pass_without_mutating_raw_tree(self) -> None:
        before = sorted(
            (path.relative_to(VENDOR).as_posix(), sha256(path.read_bytes()).hexdigest())
            for path in VENDOR.rglob("*") if path.is_file()
        )
        result = run_stage0_author_controls(VENDOR)
        after = sorted(
            (path.relative_to(VENDOR).as_posix(), sha256(path.read_bytes()).hexdigest())
            for path in VENDOR.rglob("*") if path.is_file()
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["controls_run"], 3)
        self.assertEqual(result["controls_passed"], 3)
        self.assertEqual(result["settings"], {"basic": True, "mark_compound": True})
        self.assertEqual(set(result["environment"]), {"python_version", "pandas_version"})
        self.assertEqual(before, after)
        self.assertFalse(any(path.name == "__pycache__" for path in VENDOR.rglob("*")))

    def test_stage0_calls_only_the_three_allowlisted_author_inputs(self) -> None:
        calls: list[tuple[str, str]] = []

        def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            self.assertIn("-B", args)
            input_path = Path(args[-2])
            output_path = Path(args[-1])
            relative_input = input_path.relative_to(VENDOR).as_posix()
            expected_outputs = dict(AUTHOR_CONTROLS)
            self.assertIn(relative_input, expected_outputs)
            expected_output = expected_outputs[relative_input]
            output_path.write_bytes((VENDOR / expected_output).read_bytes())
            calls.append((relative_input, expected_output))
            stdout = json.dumps({
                "python_version": "3.test",
                "pandas_version": "2.test",
                "basic": True,
                "mark_compound": True,
            })
            return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

        with patch(
            "voynich.naibbe_coverage.locate_pandas_python",
            return_value=(Path("/not-executed/python"), {
                "python_version": "3.test",
                "pandas_version": "2.test",
                "interpreter_source": "test",
            }),
        ), patch("voynich.naibbe_coverage.subprocess.run", side_effect=fake_run):
            result = run_stage0_author_controls(VENDOR)

        self.assertTrue(result["passed"])
        self.assertEqual(calls, list(AUTHOR_CONTROLS))
        self.assertFalse(any("transcriptions" in item for call in calls for item in call))

    def test_stage0_rejects_any_new_file_in_the_pinned_author_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h007-vendor-copy-") as temp_name:
            copied = Path(temp_name) / "vendor"
            shutil.copytree(VENDOR, copied)
            copied = copied.resolve()
            calls = 0

            def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                nonlocal calls
                calls += 1
                input_path = Path(args[-2])
                output_path = Path(args[-1])
                relative_input = input_path.relative_to(copied).as_posix()
                output_path.write_bytes((copied / dict(AUTHOR_CONTROLS)[relative_input]).read_bytes())
                if calls == 1:
                    (copied / "unexpected-side-effect.bin").write_bytes(b"not allowed")
                stdout = json.dumps({
                    "python_version": "3.test",
                    "pandas_version": "2.test",
                    "basic": True,
                    "mark_compound": True,
                })
                return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

            with patch(
                "voynich.naibbe_coverage.locate_pandas_python",
                return_value=(Path("/not-executed/python"), {
                    "python_version": "3.test",
                    "pandas_version": "2.test",
                    "interpreter_source": "test",
                }),
            ), patch("voynich.naibbe_coverage.subprocess.run", side_effect=fake_run):
                with self.assertRaisesRegex(H007Stage0Error, "tree changed"):
                    run_stage0_author_controls(copied)

    def test_dependency_failure_is_sanitized_and_never_loads_table(self) -> None:
        with patch(
            "voynich.naibbe_coverage.run_stage0_author_controls",
            side_effect=H007Stage0Error("sensitive dependency detail"),
        ), patch.object(
            PublishedClassObserver,
            "from_pinned_table",
            side_effect=AssertionError("table loaded after Stage 0 failure"),
        ) as table_loader:
            report = build_h007_report(PROTOCOL, ZL, IT, VENDOR, ROOT)
        table_loader.assert_not_called()
        self.assertEqual(report["disposition"], "inconclusive_stage0")
        self.assertEqual(report["stage0_author_controls"]["failure_code"], "stage0_failed")
        self.assertNotIn("sensitive dependency detail", json.dumps(report))
        self.assertFalse(report["coverage"]["discovery"]["evaluated"])
        self.assertNotIn("histogram", report["coverage"]["holdout"])


class H007ObserverTests(unittest.TestCase):
    def test_all_six_classes_and_priority_are_exhaustive(self) -> None:
        cases = {
            "U": (
                PublishedClassObserver(
                    {"ab": "U_CANARY"}, {"a": "P"}, {"b": "S"}, {"ab", "a", "b"}
                ),
                "ab",
            ),
            "B1": (PublishedClassObserver({}, {"a": "P"}, {"b": "S"}, {"a", "b"}), "ab"),
            "BA": (
                PublishedClassObserver(
                    {}, {"a": "P1", "ab": "P2"}, {"bc": "S1", "c": "S2"}, set()
                ),
                "abc",
            ),
            "C1": (PublishedClassObserver({"x": "L", "y": "R"}, {}, {}, {"x", "y"}), "xy"),
            "CA": (
                PublishedClassObserver(
                    {"x": "L", "xy": "LL", "yz": "RR", "z": "R"},
                    {}, {}, {"x", "xy", "yz", "z"},
                ),
                "xyz",
            ),
            "X": (PublishedClassObserver({}, {}, {}, set()), "uncovered"),
        }
        self.assertEqual(set(cases), set(CLASS_IDS))
        for expected, (observer, token) in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(observer.classify(token), expected)

    def test_bigram_dedup_and_compound_non_dedup_match_author_flow(self) -> None:
        dedup = PublishedClassObserver(
            {},
            {"a": "P", "ab": "P"},
            {"bc": "S", "c": "S"},
            set(),
        )
        self.assertEqual(dedup.classify("abc"), "B1")

        compound = PublishedClassObserver(
            {"x": "L", "xy": "L", "yz": "R", "z": "R"},
            {}, {}, {"x", "xy", "yz", "z"},
        )
        self.assertEqual(compound.classify("xyz"), "CA")

    def test_ambiguous_child_is_ca_and_compound_is_not_recursive(self) -> None:
        ambiguous_child = PublishedClassObserver(
            {"z": "Z"},
            {"a": "P1", "ab": "P2"},
            {"bc": "S1", "c": "S2"},
            {"abc", "z"},
        )
        self.assertEqual(ambiguous_child.classify("abcz"), "CA")

        no_recursion = PublishedClassObserver(
            {"x": "X", "y": "Y", "z": "Z"}, {}, {}, {"x", "y", "z"}
        )
        self.assertEqual(no_recursion.classify("xyz"), "X")

    def test_pinned_table_geometry_and_last_row_wins(self) -> None:
        maps, geometry = _load_published_maps(TABLE.read_bytes())
        self.assertEqual(geometry, {
            "role_entries": 414,
            "unigram_entries": 138,
            "prefix_entries": 138,
            "suffix_entries": 138,
            "tables": 6,
            "opaque_plaintext_labels": 23,
            "distinct_ciphertext_strings": 356,
        })
        rows = list(csv.DictReader(io.StringIO(TABLE.read_text(encoding="utf-8-sig"))))
        unigram_rows = [row for row in rows if row["code"].startswith("unigram_")]
        duplicate = next(
            glyph for glyph in {row["glyphs"] for row in unigram_rows}
            if sum(row["glyphs"] == glyph for row in unigram_rows) > 1
        )
        last_label = [
            row["code"].rsplit("_", 1)[1]
            for row in unigram_rows if row["glyphs"] == duplicate
        ][-1]
        self.assertEqual(maps.unigram[duplicate], last_label)

    def test_forward_atom_closure_is_intrinsically_non_unique(self) -> None:
        rows = list(
            csv.DictReader(io.StringIO(TABLE.read_text(encoding="utf-8-sig")))
        )
        roles: dict[str, list[tuple[str, str]]] = {
            "unigram": [],
            "prefix": [],
            "suffix": [],
        }
        for row in rows:
            role, _table, label = row["code"].split("_")
            roles[role].append((row["glyphs"], label))

        unigram_strings = {glyph for glyph, _label in roles["unigram"]}
        atoms: dict[str, set[str]] = {}
        for glyph, label in roles["unigram"]:
            atoms.setdefault(glyph, set()).add(label)
        for prefix, first in roles["prefix"]:
            for suffix, second in roles["suffix"]:
                glyph = prefix + suffix
                if glyph not in unigram_strings:
                    atoms.setdefault(glyph, set()).add(first + second)

        multiplicities = Counter(len(outputs) for outputs in atoms.values())
        self.assertEqual(len(atoms), 18_947)
        self.assertEqual(multiplicities, {1: 18_848, 2: 95, 3: 4})

        def multi_atom_outputs(token: str) -> set[str]:
            states: list[set[tuple[str, int]]] = [
                set() for _ in range(len(token) + 1)
            ]
            states[0].add(("", 0))
            for start in range(len(token)):
                for prefix, count in states[start]:
                    for end in range(start + 1, len(token) + 1):
                        for output in atoms.get(token[start:end], ()):
                            states[end].add((prefix + output, count + 1))
            return {output for output, count in states[-1] if count >= 2}

        ambiguous_closure_lengths = [
            len(token)
            for token, direct_outputs in atoms.items()
            if multi_atom_outputs(token) - direct_outputs
        ]
        self.assertEqual(len(ambiguous_closure_lengths), 14_648)
        self.assertEqual(min(ambiguous_closure_lengths), 2)


class H007SealingAndLeakageTests(unittest.TestCase):
    def _failure_observer(self, failure_class: str) -> tuple[PublishedClassObserver, str]:
        if failure_class == "X":
            return PublishedClassObserver({}, {}, {}, set()), "bad_x"
        if failure_class == "BA":
            return PublishedClassObserver(
                {}, {"a": "P1", "ab": "P2"}, {"bc": "S1", "c": "S2"}, set()
            ), "abc"
        if failure_class == "CA":
            return PublishedClassObserver(
                {"x": "L", "xy": "LL", "yz": "RR", "z": "R"},
                {}, {}, {"x", "xy", "yz", "z"},
            ), "xyz"
        raise AssertionError("bad test class")

    def test_x_ba_and_ca_each_poison_holdout_without_zero_histogram(self) -> None:
        for failure_class in ("X", "BA", "CA"):
            with self.subTest(failure_class=failure_class):
                base, discovery_token = self._failure_observer(failure_class)
                seen: list[str] = []

                class Guard:
                    def classify(self, token: str) -> str:
                        if token == "SEALED_HOLDOUT_CANARY":
                            raise AssertionError("held-out token met observer")
                        seen.append(token)
                        return base.classify(token)

                result = run_coverage_screen(
                    (
                        _line("f1", (discovery_token,)),
                        _line("f4", ("SEALED_HOLDOUT_CANARY",)),
                    ),
                    Guard(),  # type: ignore[arg-type]
                )
                self.assertEqual(seen, [discovery_token])
                self.assertEqual(result["discovery"]["histogram"][failure_class]["occurrences"], 1)
                self.assertFalse(result["discovery_gate_met"])
                self.assertTrue(result["holdout"]["sealed"])
                self.assertFalse(result["holdout"]["evaluated"])
                self.assertNotIn("histogram", result["holdout"])

    def test_discovery_completes_after_first_contradiction(self) -> None:
        base = PublishedClassObserver({"good": "LABEL"}, {}, {}, {"good"})
        seen: list[str] = []

        class Spy:
            def classify(self, token: str) -> str:
                seen.append(token)
                return base.classify(token)

        result = run_coverage_screen(
            (_line("f1", ("bad", "good", "bad2")),), Spy()  # type: ignore[arg-type]
        )
        self.assertEqual(seen, ["bad", "good", "bad2"])
        self.assertEqual(result["discovery"]["token_occurrences"], 3)
        self.assertEqual(result["discovery"]["histogram"]["X"]["occurrences"], 2)

    def test_frozen_inventory_is_rechecked_before_first_holdout_call(self) -> None:
        base = PublishedClassObserver({"good": "LABEL", "held": "LABEL"}, {}, {}, {"good", "held"})
        seen: list[str] = []

        class Spy:
            def classify(self, token: str) -> str:
                seen.append(token)
                return base.classify(token)

        with self.assertRaisesRegex(H007InputError, "table was not loaded"):
            run_coverage_screen(
                (_line("f1", ("good",)), _line("f4", ("held",))),
                Spy(),  # type: ignore[arg-type]
                {},
            )
        self.assertEqual(seen, ["good"])

    def test_public_schema_and_label_token_hash_canaries_do_not_leak(self) -> None:
        source_canaries = (
            "SOURCE_TOKEN_CANARY_A",
            "SOURCE_TOKEN_CANARY_B",
            "SOURCE_TOKEN_CANARY_UNCOVERED",
        )
        label_canaries = ("PLAINTEXT_LABEL_CANARY_A", "PLAINTEXT_LABEL_CANARY_B")
        observer = PublishedClassObserver(
            {source_canaries[0]: label_canaries[0], source_canaries[1]: label_canaries[1]},
            {}, {}, set(source_canaries),
        )
        coverage = run_coverage_screen((_line("f1", source_canaries),), observer)
        report = _assemble_h007_report(
            {"protocol": {"path": "notes/hypotheses/frozen.md", "sha256": "0" * 64}},
            {
                "overall": {
                    "logical_lines": 1, "page_panel_ids": 1, "physical_folios": 1,
                    "token_occurrences": 3, "distinct_token_types": 3,
                },
                "discovery": {
                    "logical_lines": 1, "page_panel_ids": 1, "physical_folios": 1,
                    "token_occurrences": 3, "distinct_token_types": 3,
                },
                "holdout": {
                    "logical_lines": 0, "page_panel_ids": 0, "physical_folios": 0,
                    "token_occurrences": 0, "distinct_token_types": 0,
                },
            },
            {"passed": True},
            {"role_entries": 1},
            coverage,
        )
        encoded = canonical_json_bytes(report)
        markdown = render_h007_markdown(report, sha256(encoded).hexdigest())
        haystack = encoded.decode("utf-8") + markdown
        for canary in (*source_canaries, *label_canaries):
            self.assertNotIn(canary, haystack)
            self.assertNotIn(sha256(canary.encode()).hexdigest(), haystack)
        self.assertEqual(set(report), {
            "analysis_version", "claim_scope", "inputs", "settings",
            "table_independent_inventory", "stage0_author_controls",
            "published_table_integrity", "coverage", "disposition",
        })
        self.assertEqual(set(report["coverage"]), {
            "discovery", "discovery_gate_met", "holdout",
            "separate_output_protocol_authorized", "decoded_output_released",
            "disposition",
        })
        self.assertNotIn("histogram", report["coverage"]["holdout"])
        self.assertNotIn("p_value", haystack)

    def test_pipeline_call_order_is_inventory_stage0_table_then_coverage(self) -> None:
        events: list[str] = []
        real_inventory = require_frozen_corpus_inventory

        def inventory_wrapper(lines: object, expected: object = FROZEN_CORPUS_INVENTORY) -> object:
            events.append("inventory")
            return real_inventory(lines, expected)  # type: ignore[arg-type]

        def fake_stage0(*args: object, **kwargs: object) -> dict[str, object]:
            events.append("stage0")
            return {"passed": True, "controls_run": 3, "controls_passed": 3}

        def fake_table(table_bytes: bytes) -> tuple[PublishedClassObserver, dict[str, int]]:
            events.append("table")
            return PublishedClassObserver({}, {}, {}, set()), {"role_entries": 414}

        def fake_coverage(*args: object, **kwargs: object) -> dict[str, object]:
            events.append("coverage")
            return _sealed_coverage("rejected_on_discovery")

        with patch(
            "voynich.naibbe_coverage.require_frozen_corpus_inventory",
            side_effect=inventory_wrapper,
        ), patch(
            "voynich.naibbe_coverage.run_stage0_author_controls",
            side_effect=fake_stage0,
        ), patch.object(
            PublishedClassObserver,
            "from_pinned_table",
            side_effect=fake_table,
        ), patch(
            "voynich.naibbe_coverage.run_coverage_screen",
            side_effect=fake_coverage,
        ):
            report = build_h007_report(PROTOCOL, ZL, IT, VENDOR, ROOT)
        self.assertEqual(events, ["inventory", "stage0", "table", "coverage"])
        self.assertEqual(report["disposition"], "rejected_on_discovery")

    def test_canonical_json_markdown_sidecar_and_paths(self) -> None:
        report = _assemble_h007_report(
            {"protocol": {"path": "notes/frozen.md", "sha256": "a" * 64}},
            {
                "overall": {
                    "logical_lines": 1, "page_panel_ids": 1, "physical_folios": 1,
                    "token_occurrences": 1, "distinct_token_types": 1,
                },
                "discovery": {
                    "logical_lines": 1, "page_panel_ids": 1, "physical_folios": 1,
                    "token_occurrences": 1, "distinct_token_types": 1,
                },
                "holdout": {
                    "logical_lines": 0, "page_panel_ids": 0, "physical_folios": 0,
                    "token_occurrences": 0, "distinct_token_types": 0,
                },
            },
            {"passed": False},
            None,
            _sealed_coverage("inconclusive_stage0"),
        )
        data = canonical_json_bytes(report)
        digest = sha256(data).hexdigest()
        self.assertEqual(data, canonical_json_bytes(json.loads(data)))
        markdown = render_h007_markdown(report, digest)
        self.assertTrue(markdown.endswith("\n"))
        self.assertIn("author-control stage did not pass", markdown)
        self.assertNotIn("because the discovery gates failed", markdown)
        self.assertEqual(render_sha256_sidecar(digest, "result.json"), f"{digest}  result.json\n")
        self.assertFalse(Path(report["inputs"]["protocol"]["path"]).is_absolute())

    def test_production_artifacts_match_except_recorded_runtime_and_remain_sealed(self) -> None:
        report = build_h007_report(PROTOCOL, ZL, IT, VENDOR, ROOT)
        retained_bytes = (ROOT / "results/h007-pk23-coverage.json").read_bytes()
        retained = json.loads(retained_bytes)
        retained_hash = sha256(retained_bytes).hexdigest()
        self.assertEqual(
            retained_hash,
            "174e0469312cfbe2d19fe8ad8f435fbd6453a7af9ba1305300140757519b46fd",
        )
        # The scientific output is fixed; actual runtime version strings are
        # evidence and can differ on another machine. Keep the historical JSON
        # untouched and require exact equality after replacing only this field.
        runtime = report["stage0_author_controls"]["environment"]
        self.assertEqual(set(runtime), {"python_version", "pandas_version"})
        self.assertTrue(all(isinstance(value, str) and value for value in runtime.values()))
        compared = json.loads(canonical_json_bytes(report))
        compared["stage0_author_controls"]["environment"] = retained["stage0_author_controls"]["environment"]
        self.assertEqual(canonical_json_bytes(compared), retained_bytes)
        self.assertEqual(
            (ROOT / "results/h007-pk23-coverage.md").read_text(encoding="utf-8"),
            render_h007_markdown(retained, retained_hash),
        )
        self.assertEqual(
            (ROOT / "results/h007-pk23-coverage.sha256.txt").read_text(encoding="ascii"),
            render_sha256_sidecar(retained_hash, "h007-pk23-coverage.json"),
        )
        self.assertEqual(report["disposition"], "rejected_on_discovery")
        self.assertEqual(
            {
                class_id: report["coverage"]["discovery"]["histogram"][class_id][
                    "occurrences"
                ]
                for class_id in CLASS_IDS
            },
            {"U": 797, "B1": 937, "BA": 82, "C1": 27, "CA": 3, "X": 495},
        )
        self.assertFalse(report["coverage"]["discovery_gate_met"])
        self.assertEqual(
            report["coverage"]["holdout"],
            {
                "evaluated": False,
                "sealed": True,
                "aggregate_histogram_reported": False,
            },
        )
        self.assertFalse(report["coverage"]["decoded_output_released"])


if __name__ == "__main__":
    unittest.main()
