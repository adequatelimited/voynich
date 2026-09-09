from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.ivtff import parse_ivtff
from voynich.ternary_frame import (
    ANALYSIS_VERSION,
    IT_EVA_SHA256,
    PROTOCOL_SHA256,
    ZL_EVA_SHA256,
    EligibleLine,
    build_eligible_lines,
    build_h006_report,
    canonical_json_bytes,
    discovery_breadth_checks,
    evaluate_component_model,
    expand_sign,
    expand_tokens,
    holdout_breadth_checks,
    is_holdout_physical_folio,
    physical_folio,
    recorded_relative_path,
    require_frozen_inventory,
    render_h006_markdown,
    render_sha256_sidecar,
    run_frame_screen,
    split_inventory_summary,
)


def _document(
    records: list[tuple[int, str, str]], *, alphabet: str = "Eva-",
    metadata: str = "$I=H $L=A $H=1",
) -> object:
    lines = [
        f"#=IVTFF {alphabet} 2.0 M",
        f"<f1r> <! {metadata}>",
    ]
    lines.extend(
        f"<f1r.{number},{locator_type}> {text}"
        for number, locator_type, text in records
    )
    return parse_ivtff(("\n".join(lines) + "\n").encode("ascii"))


def _folios(*, heldout: bool, count: int) -> list[str]:
    result: list[str] = []
    index = 1
    while len(result) < count:
        folio = f"f{index}"
        if is_holdout_physical_folio(folio) is heldout:
            result.append(folio)
        index += 1
    return result


def _discovery_fixture(
    *, contradiction: bool = False, token: str = "aaa"
) -> tuple[EligibleLine, ...]:
    folios = _folios(heldout=False, count=60)
    result = []
    for index in range(800):
        result.append(
            EligibleLine(
                page_id=f"{folios[index % len(folios)]}r",
                locus_number=index + 1,
                physical_folio=folios[index % len(folios)],
                currier="A" if index < 300 else "B",
                hand="1" if index < 300 else "2" if index < 600 else "3",
                illustration=("H", "S", "B")[index % 3],
                tokens=("a",) if contradiction and index == 0 else (token,),
            )
        )
    return tuple(result)


def _holdout_fixture() -> tuple[EligibleLine, ...]:
    folios = _folios(heldout=True, count=20)
    result = []
    for index in range(250):
        result.append(
            EligibleLine(
                page_id=f"{folios[index % len(folios)]}r",
                locus_number=index + 1,
                physical_folio=folios[index % len(folios)],
                currier="A" if index < 175 else "B",
                hand="1" if index < 100 else "2" if index < 120 else "3",
                illustration=("H", "S", "B")[index % 3],
                tokens=("aaa",),
            )
        )
    return tuple(result)


class H006ExpansionTests(unittest.TestCase):
    def test_recursive_pair_and_optional_e_expansions_are_exact(self) -> None:
        self.assertEqual(expand_sign("d", "PAIR"), "ey")
        self.assertEqual(expand_sign("q", "PAIR"), "ie")
        self.assertEqual(expand_sign("f", "PAIR"), "iey")
        self.assertEqual(expand_sign("m", "PAIR"), "iey")
        self.assertEqual(expand_sign("p", "PAIR"), "ieey")
        self.assertEqual(expand_sign("t", "PAIR"), "iel")
        self.assertEqual(expand_sign("g", "PAIR"), "cey")
        self.assertEqual(expand_sign("f", "OPTIONAL_E"), "ieye")
        self.assertEqual(expand_sign("p", "OPTIONAL_E"), "ieeye")
        self.assertEqual(expand_tokens(("dn", "a"), "PAIR"), "eyia")

    def test_expansion_rejects_out_of_inventory_and_unknown_model(self) -> None:
        with self.assertRaises(ValueError):
            expand_sign("v", "PAIR")
        with self.assertRaises(ValueError):
            expand_sign("a", "invented")


class H006EligibilityTests(unittest.TestCase):
    def test_strict_exact_consensus_and_word_final_n_gate(self) -> None:
        zl = _document(
            [
                (1, "@P0", "dain.ol"),
                (2, "@P0", "dani"),
                (3, "@P0", "daiin"),
                (4, "@P0", "daiin,ol"),
                (5, "@P0", "da'in"),
                (6, "@P0", "daiuv"),
                (7, "!P0", "daiin"),
                (8, "@Lf", "daiin"),
                (9, "@P0", "daiin"),
                (10, "@P0", "nn"),
            ]
        )
        it = _document(
            [
                (1, "@P0", "dain.ol"),
                (2, "@P0", "dani"),
                (3, "@P0", "dain"),
                (4, "@P0", "daiin,ol"),
                (5, "@P0", "da'in"),
                (6, "@P0", "daiuv"),
                (7, "@P0", "daiin"),
                (8, "@Lf", "daiin"),
                (10, "@P0", "nn"),
            ],
            alphabet="EvaT",
        )
        eligible, audits = build_eligible_lines(zl, it)
        self.assertEqual([line.line_id for line in eligible], ["f1r.1"])
        by_id = {audit.line_id: audit for audit in audits}
        self.assertIn("midword_n", by_id["f1r.2"].reasons)
        self.assertIn("zl_it_token_disagreement", by_id["f1r.3"].reasons)
        self.assertIn("zl_excluded:uncertain_word_space", by_id["f1r.4"].reasons)
        self.assertIn("zl_excluded:apostrophe", by_id["f1r.5"].reasons)
        self.assertIn("outside_frozen_sign_inventory", by_id["f1r.6"].reasons)
        self.assertIn("invalid_locator", by_id["f1r.7"].reasons)
        self.assertIn("nonprose_locus", by_id["f1r.8"].reasons)
        self.assertIn("missing_or_duplicate_it_locus", by_id["f1r.9"].reasons)
        self.assertIn("midword_n", by_id["f1r.10"].reasons)

    def test_braces_are_normalized_audited_and_logical_continuations_stay_one_line(self) -> None:
        zl_raw = (
            b"#=IVTFF Eva- 2.0 M\n"
            b"<f1r> <! $I=H $L=A $H=1>\n"
            b"<f1r.1,@P0> {da}/\n"
            b"/in.ol\n"
        )
        it_raw = (
            b"#=IVTFF EvaT 2.0 M\n"
            b"<f1r> <! $I=H $L=A $H=1>\n"
            b"<f1r.1,@P0> dain.ol\n"
        )
        eligible, audits = build_eligible_lines(parse_ivtff(zl_raw), parse_ivtff(it_raw))
        self.assertEqual(len(eligible), 1)
        self.assertEqual(eligible[0].tokens, ("dain", "ol"))
        self.assertEqual(len(eligible), len({line.line_id for line in eligible}))
        self.assertTrue(audits[0].zl_brace_notation_present)
        self.assertFalse(audits[0].it_brace_notation_present)

    def test_braces_inside_inert_comments_do_not_enter_the_ligature_audit(self) -> None:
        zl = _document([(1, "@P0", "dain<! editorial {note}>.ol")])
        it = _document([(1, "@P0", "dain.ol")], alphabet="EvaT")
        eligible, audits = build_eligible_lines(zl, it)
        self.assertEqual(len(eligible), 1)
        self.assertFalse(audits[0].zl_brace_notation_present)
        self.assertFalse(audits[0].it_brace_notation_present)

    def test_it_header_and_exact_zl_metadata_domains_are_enforced(self) -> None:
        valid_zl = _document([(1, "@P0", "dain")])
        wrong_it = _document([(1, "@P0", "dain")], alphabet="Eva-")
        with self.assertRaisesRegex(ValueError, "IT alphabet EvaT"):
            build_eligible_lines(valid_zl, wrong_it)

        for metadata in ("$I=Q $L=A $H=1", "$I=H $L=C $H=1", "$I=H $L=A $H=6"):
            with self.subTest(metadata=metadata):
                zl = _document([(1, "@P0", "dain")], metadata=metadata)
                it = _document([(1, "@P0", "dain")], alphabet="EvaT")
                eligible, audits = build_eligible_lines(zl, it)
                self.assertEqual(eligible, ())
                self.assertIn(
                    "zl_metadata_outside_frozen_domains", audits[0].reasons
                )

    def test_physical_folio_and_split_keep_panels_together(self) -> None:
        self.assertEqual(physical_folio("f90r2"), "f90")
        self.assertEqual(physical_folio("f90v1"), "f90")
        with self.assertRaises(ValueError):
            physical_folio("fRos")
        folio = "f90"
        expected = sha256(f"{ANALYSIS_VERSION}:{folio}".encode("ascii")).digest()[0] < 51
        self.assertEqual(is_holdout_physical_folio(folio), expected)
        self.assertFalse(is_holdout_physical_folio("f1"))
        self.assertTrue(is_holdout_physical_folio("f4"))


class H006GateTests(unittest.TestCase):
    def test_exact_all_lines_gate_and_frozen_breadth(self) -> None:
        clean = _discovery_fixture()
        self.assertTrue(all(discovery_breadth_checks(clean).values()))
        clean_result = evaluate_component_model(clean, "PAIR")
        self.assertTrue(clean_result["deterministic_residue_gate_met"])
        self.assertEqual(clean_result["overall"]["zero_residue_fraction"], 1.0)
        self.assertEqual(clean_result["overall"]["contradictions"], 0)
        self.assertFalse(clean_result["p_value_computed"])
        self.assertFalse(clean_result["null_model_computed"])

        contradicted = _discovery_fixture(contradiction=True)
        result = evaluate_component_model(contradicted, "PAIR")
        self.assertFalse(result["deterministic_residue_gate_met"])
        self.assertEqual(result["overall"]["contradictions"], 1)
        self.assertEqual(result["overall"]["histogram"], {"0": 799, "1": 1, "2": 0})

    def test_holdout_breadth_and_pair_tie_break(self) -> None:
        discovery = _discovery_fixture()
        holdout = _holdout_fixture()
        self.assertTrue(all(holdout_breadth_checks(holdout).values()))
        result = run_frame_screen((*discovery, *holdout))
        self.assertEqual(result["discovery"]["qualifying_models"], ["PAIR", "OPTIONAL_E"])
        self.assertEqual(result["discovery"]["locked_model"], "PAIR")
        self.assertTrue(result["holdout"]["residue_evaluated"])
        self.assertTrue(result["holdout_gate_met"])
        self.assertTrue(result["key_plaintext_stage_authorized"])

    def test_discovery_failure_never_reads_or_reports_holdout_residue(self) -> None:
        class ExplodingTokens:
            def __iter__(self):
                raise AssertionError("sealed holdout tokens were inspected")

        discovery_folio = _folios(heldout=False, count=1)[0]
        holdout_folio = _folios(heldout=True, count=1)[0]
        discovery = EligibleLine(
            f"{discovery_folio}r", 1, discovery_folio, "A", "1", "H", ("a",)
        )
        sealed = EligibleLine(
            f"{holdout_folio}r",
            1,
            holdout_folio,
            "A",
            "1",
            "H",
            ExplodingTokens(),
        )
        result = run_frame_screen((discovery, sealed))
        self.assertIsNone(result["discovery"]["locked_model"])
        self.assertFalse(result["discovery"]["residue_evaluated"])
        self.assertIn("inconclusive", result["disposition"])
        self.assertTrue(result["holdout"]["sealed"])
        self.assertFalse(result["holdout"]["residue_evaluated"])
        self.assertFalse(result["holdout"]["residue_reported"])
        self.assertNotIn("locked_model_result", result["holdout"])

    def test_breadth_pass_but_both_models_fail_keeps_holdout_sealed(self) -> None:
        class ExplodingTokens:
            def __iter__(self):
                raise AssertionError("rejected discovery opened held-out tokens")

        holdout_folio = _folios(heldout=True, count=1)[0]
        sealed = EligibleLine(
            f"{holdout_folio}r", 1, holdout_folio, "A", "1", "H", ExplodingTokens()
        )
        result = run_frame_screen((*_discovery_fixture(contradiction=True), sealed))
        self.assertTrue(result["discovery"]["breadth_gate_met"])
        self.assertEqual(result["discovery"]["qualifying_models"], [])
        self.assertIn("reject", result["disposition"])
        self.assertTrue(result["holdout"]["sealed"])
        self.assertFalse(result["holdout"]["residue_evaluated"])

    def test_holdout_breadth_failure_keeps_qualified_model_residues_sealed(self) -> None:
        class ExplodingTokens:
            def __iter__(self):
                raise AssertionError("breadth-failed holdout tokens were inspected")

        holdout_folio = _folios(heldout=True, count=1)[0]
        sealed = EligibleLine(
            f"{holdout_folio}r", 1, holdout_folio, "A", "1", "H", ExplodingTokens()
        )
        result = run_frame_screen((*_discovery_fixture(token="f"), sealed))
        self.assertEqual(result["discovery"]["qualifying_models"], ["PAIR"])
        self.assertEqual(result["discovery"]["locked_model"], "PAIR")
        self.assertFalse(result["holdout"]["breadth_gate_met"])
        self.assertFalse(result["holdout"]["residue_evaluated"])
        self.assertIn("inconclusive", result["disposition"])

    def test_only_pair_reaches_holdout_and_full_histogram_does_not_stop_early(self) -> None:
        inspections = [0] * 250

        class CountingTokens:
            def __init__(self, index: int, token: str) -> None:
                self.index = index
                self.token = token

            def __iter__(self):
                inspections[self.index] += 1
                yield self.token

        holdout = []
        for index, line in enumerate(_holdout_fixture()):
            holdout.append(
                EligibleLine(
                    line.page_id,
                    line.locus_number,
                    line.physical_folio,
                    line.currier,
                    line.hand,
                    line.illustration,
                    CountingTokens(index, "a" if index == 0 else "aaa"),
                )
            )
        result = run_frame_screen((*_discovery_fixture(token="f"), *holdout))
        self.assertEqual(result["discovery"]["qualifying_models"], ["PAIR"])
        self.assertEqual(
            result["holdout"]["locked_model_result"]["model_id"], "PAIR"
        )
        self.assertEqual(
            result["holdout"]["locked_model_result"]["overall"]["histogram"],
            {"0": 249, "1": 1, "2": 0},
        )
        self.assertEqual(inspections, [1] * 250)
        self.assertFalse(result["holdout_gate_met"])


class H006ArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.zl = _document([(1, "@P0", "dain.ol")])
        self.it = _document([(1, "@P0", "dain.ol")], alphabet="EvaT")
        self.protocol_bytes = b"synthetic frozen H006 protocol\n"
        self.expected = {
            "_expected_protocol_sha256": sha256(self.protocol_bytes).hexdigest(),
            "_expected_zl_sha256": sha256(self.zl.source).hexdigest(),
            "_expected_it_sha256": sha256(self.it.source).hexdigest(),
        }
        lines, _ = build_eligible_lines(self.zl, self.it)
        self.synthetic_inventory = split_inventory_summary(lines)

    def test_pinned_input_hash_constants_match_files_without_running_analysis(self) -> None:
        self.assertEqual(
            sha256((ROOT / "data/raw/transcriptions/ZL3b-n.txt").read_bytes()).hexdigest(),
            ZL_EVA_SHA256,
        )
        self.assertEqual(
            sha256((ROOT / "data/raw/transcriptions/IT2a-n.txt").read_bytes()).hexdigest(),
            IT_EVA_SHA256,
        )
        self.assertEqual(
            sha256(
                (ROOT / "notes/hypotheses/H006-FR3-line-reset-ternary-code.md").read_bytes()
            ).hexdigest(),
            PROTOCOL_SHA256,
        )

    def test_production_artifacts_are_fresh_deterministic_and_sealed(self) -> None:
        protocol_path = ROOT / "notes/hypotheses/H006-FR3-line-reset-ternary-code.md"
        zl_path = ROOT / "data/raw/transcriptions/ZL3b-n.txt"
        it_path = ROOT / "data/raw/transcriptions/IT2a-n.txt"
        report = build_h006_report(
            protocol_path.read_bytes(), zl_path.read_bytes(), it_path.read_bytes()
        )
        report["inputs"]["protocol"]["path"] = recorded_relative_path(
            protocol_path, ROOT
        )
        report["inputs"]["zl_eva"]["path"] = recorded_relative_path(zl_path, ROOT)
        report["inputs"]["it_eva"]["path"] = recorded_relative_path(it_path, ROOT)

        report_bytes = canonical_json_bytes(report)
        report_hash = sha256(report_bytes).hexdigest()
        self.assertEqual(
            (ROOT / "results/h006-fr3-line-reset.json").read_bytes(), report_bytes
        )
        self.assertEqual(
            (ROOT / "results/h006-fr3-line-reset.md").read_text(encoding="utf-8"),
            render_h006_markdown(report, report_hash),
        )
        self.assertEqual(
            (ROOT / "results/h006-fr3-line-reset.sha256.txt").read_text(
                encoding="ascii"
            ),
            render_sha256_sidecar(report_hash, "h006-fr3-line-reset.json"),
        )
        self.assertEqual(
            report_hash,
            "192845597048b3655debadd50661bebdf08b741bb28ecb23146811a59fc963c7",
        )
        self.assertEqual(report["screen"]["discovery"]["qualifying_models"], [])
        self.assertTrue(report["screen"]["holdout"]["sealed"])
        self.assertFalse(report["screen"]["holdout"]["residue_evaluated"])
        self.assertNotIn("locked_model_result", report["screen"]["holdout"])

    def test_hash_mismatch_fails_before_analysis(self) -> None:
        with self.assertRaisesRegex(ValueError, "protocol SHA-256"):
            build_h006_report(
                self.protocol_bytes,
                self.zl.source,
                self.it.source,
                _expected_protocol_sha256="0" * 64,
                _expected_zl_sha256=self.expected["_expected_zl_sha256"],
                _expected_it_sha256=self.expected["_expected_it_sha256"],
            )

        malformed = b"not an IVTFF document\n"
        with self.assertRaisesRegex(ValueError, "zl_eva SHA-256"):
            build_h006_report(
                self.protocol_bytes,
                malformed,
                self.it.source,
                _expected_protocol_sha256=self.expected[
                    "_expected_protocol_sha256"
                ],
                _expected_zl_sha256="0" * 64,
                _expected_it_sha256=self.expected["_expected_it_sha256"],
            )

    def test_frozen_inventory_guard_aborts_synthetic_mismatch_before_expansion(self) -> None:
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            build_h006_report(
                self.protocol_bytes,
                self.zl.source,
                self.it.source,
                **self.expected,
            )
        lines, _ = build_eligible_lines(self.zl, self.it)
        self.assertEqual(
            require_frozen_inventory(lines, self.synthetic_inventory),
            self.synthetic_inventory,
        )

    def test_inventory_mismatch_does_not_inspect_line_tokens(self) -> None:
        class ExplodingTokens:
            def __iter__(self):
                raise AssertionError("inventory guard expanded a line")

        line = EligibleLine("f1r", 1, "f1", "A", "1", "H", ExplodingTokens())
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            require_frozen_inventory((line,), {"overall": {}, "discovery": {}, "holdout": {}})

    def test_all_raw_hashes_are_checked_before_any_parse(self) -> None:
        with patch(
            "voynich.ternary_frame.parse_ivtff",
            side_effect=AssertionError("parser was called before all hashes passed"),
        ):
            with self.assertRaisesRegex(ValueError, "it_eva SHA-256"):
                build_h006_report(
                    self.protocol_bytes,
                    self.zl.source,
                    self.it.source,
                    _expected_protocol_sha256=self.expected[
                        "_expected_protocol_sha256"
                    ],
                    _expected_zl_sha256=self.expected["_expected_zl_sha256"],
                    _expected_it_sha256="0" * 64,
                )

    def test_byte_identical_emit_is_checked_before_eligibility(self) -> None:
        class NonIdenticalEmitDocument:
            def __init__(self, document: object) -> None:
                self.header = document.header

            def emit(self) -> bytes:
                return b"not the supplied bytes"

        with patch(
            "voynich.ternary_frame.parse_ivtff",
            side_effect=[NonIdenticalEmitDocument(self.zl), self.it],
        ), patch(
            "voynich.ternary_frame.build_eligible_lines",
            side_effect=AssertionError("eligibility ran after emit mismatch"),
        ):
            with self.assertRaisesRegex(ValueError, "did not emit its exact input bytes"):
                build_h006_report(
                    self.protocol_bytes,
                    self.zl.source,
                    self.it.source,
                    _expected_inventory=self.synthetic_inventory,
                    **self.expected,
                )

    def test_report_builder_enforces_it_header_after_raw_hashes(self) -> None:
        wrong_it = _document([(1, "@P0", "dain.ol")], alphabet="Eva-")
        with self.assertRaisesRegex(ValueError, "IT IVTFF alphabet"):
            build_h006_report(
                self.protocol_bytes,
                self.zl.source,
                wrong_it.source,
                _expected_protocol_sha256=self.expected[
                    "_expected_protocol_sha256"
                ],
                _expected_zl_sha256=self.expected["_expected_zl_sha256"],
                _expected_it_sha256=sha256(wrong_it.source).hexdigest(),
                _expected_inventory=self.synthetic_inventory,
            )

    def test_synthetic_json_markdown_and_sidecar_are_canonical(self) -> None:
        report = build_h006_report(
            self.protocol_bytes,
            self.zl.source,
            self.it.source,
            _expected_inventory=self.synthetic_inventory,
            **self.expected,
        )
        report_bytes = canonical_json_bytes(report)
        report_hash = sha256(report_bytes).hexdigest()
        markdown = render_h006_markdown(report, report_hash)
        sidecar = render_sha256_sidecar(report_hash, "synthetic-h006.json")

        self.assertEqual(report_bytes, canonical_json_bytes(json.loads(report_bytes)))
        self.assertIn("remain sealed", markdown)
        self.assertIn("No iid", markdown)
        self.assertIn("Exclusion counts are multi-label", markdown)
        self.assertIn("Keys with ZL brace notation", markdown)
        self.assertEqual(sidecar, f"{report_hash}  synthetic-h006.json\n")
        self.assertFalse(report["screen"]["holdout"]["residue_evaluated"])
        self.assertNotIn("locked_model_result", report["screen"]["holdout"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "synthetic-h006.json").write_bytes(report_bytes)
            (root / "synthetic-h006.md").write_text(markdown, encoding="utf-8")
            (root / "synthetic-h006.sha256.txt").write_text(sidecar, encoding="ascii")
            self.assertEqual((root / "synthetic-h006.json").read_bytes(), report_bytes)
            self.assertEqual((root / "synthetic-h006.md").read_text(), markdown)
            self.assertEqual((root / "synthetic-h006.sha256.txt").read_text(), sidecar)

    def test_brace_and_multi_label_attrition_are_reported(self) -> None:
        zl = _document(
            [
                (1, "@P0", "{da}in.ol"),
                (2, "@P0", "da'in,ol"),
            ]
        )
        it = _document(
            [
                (1, "@P0", "dain.ol"),
                (2, "@P0", "da'in,ol"),
            ],
            alphabet="EvaT",
        )
        protocol = b"synthetic brace and attrition protocol\n"
        eligible, _ = build_eligible_lines(zl, it)
        report = build_h006_report(
            protocol,
            zl.source,
            it.source,
            _expected_protocol_sha256=sha256(protocol).hexdigest(),
            _expected_zl_sha256=sha256(zl.source).hexdigest(),
            _expected_it_sha256=sha256(it.source).hexdigest(),
            _expected_inventory=split_inventory_summary(eligible),
        )
        brace_audit = report["eligibility"]["brace_notation_audit"]
        self.assertEqual(brace_audit["zl_keys"], 1)
        self.assertEqual(brace_audit["it_keys"], 0)
        self.assertEqual(brace_audit["admitted_either_witness_keys"], 1)
        reasons = report["eligibility"]["exclusion_reason_counts"]
        self.assertEqual(reasons["zl_excluded:apostrophe"], 1)
        self.assertEqual(reasons["zl_excluded:uncertain_word_space"], 1)
        self.assertEqual(reasons["zl_no_certain_token"], 1)
        self.assertEqual(reasons["it_excluded:apostrophe"], 1)
        self.assertEqual(reasons["it_excluded:uncertain_word_space"], 1)
        self.assertEqual(reasons["it_no_certain_token"], 1)

    def test_recorded_paths_are_repository_relative_and_cwd_independent(self) -> None:
        inside = ROOT / "data/raw/transcriptions/ZL3b-n.txt"
        outside = ROOT.parent / "external-h006-input.txt"
        self.assertEqual(
            recorded_relative_path(inside, ROOT),
            "data/raw/transcriptions/ZL3b-n.txt",
        )
        self.assertEqual(
            recorded_relative_path(outside, ROOT),
            "../external-h006-input.txt",
        )


if __name__ == "__main__":
    unittest.main()
