from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.ivtff import IVTFFParseError, iter_paragraphs, parse_ivtff, tokenize_certain_basic_eva
from voynich.analysis import (
    baseline_report,
    locus_shared_family_label_recurrence_hypothesis,
    corpus_integrity,
    h002_cross_transcription_sta1_audit,
    local_label_recurrence_hypothesis,
    sta1_glyphs,
)


class IVTFFParserTests(unittest.TestCase):
    def test_parses_metadata_tags_and_retains_source_bytes(self) -> None:
        raw = (
            b"#=IVTFF Eva- 2.0 M 5\n"
            b"# preamble\n"
            b"<f115r> <! $I=S $L=B $H=@>\n"
            b"<f115r.1,@P0> <%><@H=2>qokedy.daiin\n"
            b"<f115r.2,=Pt> chedy<$>\n"
        )
        document = parse_ivtff(raw)

        self.assertEqual(document.emit(), raw)
        self.assertEqual(document.header.alphabet, "Eva-")
        self.assertEqual(document.pages[0].variables["H"], "@")
        self.assertEqual(document.loci[0].effective_variables["H"], "2")
        self.assertEqual(document.loci[1].locus_type, "Pt")
        self.assertEqual(len(list(iter_paragraphs(document))), 1)

    def test_joins_logical_continuations_but_emits_physical_source(self) -> None:
        raw = (
            b"#=IVTFF Eva- 2.0 M\n"
            b"<fRos> <! $I=C>\n"
            b"<fRos.1,@P0;Z> <%>qokedy./\n"
            b"/chedy<$>\n"
        )
        document = parse_ivtff(raw)
        self.assertEqual(document.loci[0].text, "<%>qokedy.chedy<$>")
        self.assertEqual(len(document.loci[0].physical_lines), 2)
        self.assertEqual(document.emit(), raw)

    def test_requires_matched_paragraph_markers(self) -> None:
        raw = b"#=IVTFF Eva- 2.0 M\n<f1r>\n<f1r.1,@P0> <%>daiin\n"
        with self.assertRaises(IVTFFParseError):
            parse_ivtff(raw)

    def test_alternative_identifiers_require_no_page_headers(self) -> None:
        raw = (
            b"#=IVTFF STA1 2.0 D\n"
            b"# database export\n"
            b"<AA001> <%>A1B1.A2<$>\n"
            b"<AB001;Z> <%>K1A1B2<$>\n"
        )
        document = parse_ivtff(raw)
        self.assertEqual([page.page_id for page in document.pages], ["AA", "AB"])
        self.assertTrue(all(page.alternative_identifiers for page in document.pages))
        self.assertTrue(all(page.header_line is None for page in document.pages))
        self.assertEqual(document.loci[1].transcriber, "Z")
        self.assertEqual(document.emit(), raw)

    def test_rejects_mixed_standard_and_alternative_identifiers(self) -> None:
        raw = b"#=IVTFF Eva- 2.0 M\n<f1r>\n<AA001> daiin\n"
        with self.assertRaises(IVTFFParseError):
            parse_ivtff(raw)

    def test_free_comments_cannot_activate_embedded_controls(self) -> None:
        raw = (
            b"#=IVTFF Eva- 2.0 M\n"
            b"<f1r> <! $H=1>\n"
            b"<f1r.1,@P0> <%><! literal <@H=5>qokedy<$>\n"
        )
        document = parse_ivtff(raw)
        self.assertEqual(document.loci[0].effective_variables["H"], "1")

    def test_rejects_invalid_inline_syntax(self) -> None:
        invalid_texts = ["[ol]", "@999;", "{ch", "daiin>"]
        for text in invalid_texts:
            with self.subTest(text=text):
                raw = (
                    b"#=IVTFF Eva- 2.0 M\n<f1r>\n<f1r.1,@P0> "
                    + text.encode("ascii")
                    + b"\n"
                )
                with self.assertRaises(IVTFFParseError):
                    parse_ivtff(raw)

    def test_conservative_tokenization_explains_every_exclusion(self) -> None:
        result = tokenize_certain_basic_eva(
            "<%>qokedy.daiin,chedy.[ol:or].{cth}y.@192;ar<->shol.???.d?y<$>"
        )
        self.assertEqual(result.tokens, ("qokedy", "cthy", "shol"))
        self.assertEqual(
            [excluded.reason for excluded in result.excluded],
            [
                "uncertain_word_space",
                "alternative_reading",
                "extended_eva",
                "unreadable_glyph",
                "unreadable_glyph",
            ],
        )

    def test_conservative_tokenization_excludes_joined_capitals(self) -> None:
        result = tokenize_certain_basic_eva("daiin.chol.Iiin")
        self.assertEqual(result.tokens, ("daiin", "chol"))
        self.assertEqual(result.excluded[0].reason, "joined_eva_form")


class PinnedCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = ROOT / "data/raw/transcriptions/ZL3b-n.txt"
        cls.raw = cls.path.read_bytes()
        cls.document = parse_ivtff(cls.raw)

    def test_pinned_hash_and_source_retention(self) -> None:
        self.assertEqual(
            sha256(self.raw).hexdigest(),
            "bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc",
        )
        self.assertEqual(self.document.emit(), self.raw)

    def test_pinned_corpus_shape(self) -> None:
        self.assertEqual(len(self.document.pages), 227)
        self.assertEqual(len(self.document.loci), 5385)
        self.assertEqual(
            {
                kind: sum(locus.generic_type == kind for locus in self.document.loci)
                for kind in "PLCR"
            },
            {"P": 4130, "L": 1029, "C": 84, "R": 142},
        )
        self.assertEqual(sum(locus.paragraph_start for locus in self.document.loci), 740)
        self.assertEqual(sum(locus.paragraph_end for locus in self.document.loci), 740)

    def test_pinned_corpus_regression_counts(self) -> None:
        report = corpus_integrity(self.document)
        self.assertEqual(report["alternative_groups"], 817)
        self.assertEqual(report["uncertain_spaces"], 2748)
        self.assertEqual(report["drawing_boundaries"], {"aligned": 758, "misaligned": 6})
        self.assertEqual(report["ligature_groups"], 446)
        self.assertEqual(report["extended_eva_codes"], 178)
        self.assertEqual(report["tokens_comma_as_boundary"], 39026)
        self.assertEqual(report["tokens_comma_joined"], 36278)

    def test_sta1_glyph_count_matches_published_total(self) -> None:
        sta_path = ROOT / "data/raw/transcriptions/sta1/ZL3b.txt"
        sta_document = parse_ivtff(sta_path.read_bytes())
        self.assertEqual(sum(len(sta1_glyphs(locus)) for locus in sta_document.loci), 157304)

    def test_h002_is_deterministic_and_reports_held_out_data(self) -> None:
        first = local_label_recurrence_hypothesis(self.document)
        second = local_label_recurrence_hypothesis(self.document)
        self.assertEqual(first, second)
        self.assertEqual(first["true_label_types"], ["La", "Lc", "Lf", "Ln", "Lp", "Ls", "Lt", "Lz"])
        self.assertIn("evaluated_label_types", first["held_out"])

    def test_h002_sta1_audit_is_positional_and_fail_closed(self) -> None:
        zl = parse_ivtff((ROOT / "data/raw/transcriptions/sta1/ZL3b.txt").read_bytes())
        gc = parse_ivtff((ROOT / "data/raw/transcriptions/sta1/GC2a_0.txt").read_bytes())
        audit = h002_cross_transcription_sta1_audit(self.document, zl, gc)

        self.assertEqual(
            audit["summary"],
            {
                "held_out_hits_audited": 2,
                "all_alignments_complete": True,
                "hits_with_exact_member_support_in_both_transcriptions": 0,
                "hits_with_family_support_in_both_transcriptions": 2,
                "all_hits_have_exact_member_support_in_both_transcriptions": False,
                "all_hits_have_family_support_in_both_transcriptions": True,
            },
        )
        hits = {hit["eva_token"]: hit for hit in audit["hits"]}
        sheol = hits["sheol"]
        self.assertEqual(
            (
                sheol["label_occurrences"][0]["eva_locus"],
                sheol["label_occurrences"][0]["component_index"],
                sheol["label_occurrences"][0]["zl_sta1_word"],
                sheol["label_occurrences"][0]["gc_sta1_word"],
            ),
            ("<f89v2.5,@Lf>", 0, "L1J1A1B2", "LeJ1A3B2"),
        )
        self.assertEqual(
            (
                sheol["prose_occurrences"][0]["eva_locus"],
                sheol["prose_occurrences"][0]["component_index"],
                sheol["prose_occurrences"][0]["zl_sta1_word"],
                sheol["prose_occurrences"][0]["gc_sta1_word"],
            ),
            ("<f89v2.7,@P0>", 1, "L1J1A1B2", "L1J1A1B2"),
        )
        self.assertFalse(
            sheol["any_pair_exact_member_supported_by_both_transcriptions"]
        )
        self.assertTrue(
            sheol["any_pair_family_supported_by_both_transcriptions"]
        )

        chody = hits["chody"]
        self.assertEqual(
            [item["component_index"] for item in chody["prose_occurrences"]],
            [9, 13],
        )
        self.assertEqual(
            (
                chody["label_occurrences"][0]["zl_sta1_word"],
                chody["label_occurrences"][0]["gc_sta1_word"],
                chody["label_occurrences"][0]["zl_family"],
                chody["label_occurrences"][0]["gc_family"],
            ),
            ("K1A1B1A2", "K1A1BaA2", "KABA", "KABA"),
        )
        self.assertTrue(
            all(
                not pair["exact_member_match"]["supported_by_both_transcriptions"]
                and pair["family_match"]["supported_by_both_transcriptions"]
                for pair in chody["pair_comparisons"]
            )
        )

        baseline = baseline_report(
            self.document,
            zl_sta_document=zl,
            gc_sta_document=gc,
        )
        self.assertEqual(
            baseline["hypotheses"]["H002"]["cross_transcription_sta1_audit"],
            audit,
        )

    def test_h003_is_deterministic_and_uses_sta1(self) -> None:
        zl = parse_ivtff((ROOT / "data/raw/transcriptions/sta1/ZL3b.txt").read_bytes())
        gc = parse_ivtff((ROOT / "data/raw/transcriptions/sta1/GC2a_0.txt").read_bytes())
        first = locus_shared_family_label_recurrence_hypothesis(zl, gc)
        second = locus_shared_family_label_recurrence_hypothesis(zl, gc)
        self.assertEqual(first, second)
        self.assertEqual(first["hypothesis_id"], "H003")
        self.assertEqual(
            first["alignment"],
            {
                "zl_substantive_loci": 5385,
                "gc_substantive_loci": 5366,
                "common_loci": 5366,
                "zl_only_loci": 19,
                "gc_only_loci": 0,
                "locus_type_mismatches": 0,
                "locator_mismatches": 0,
            },
        )
        self.assertFalse(first["advancement_criterion_met"])
        self.assertIn("not an untouched holdout", first["partition_validity"])
        self.assertEqual(
            len(first["prior_h002_partition_overlap"]["also_h002_discovery_pages"]),
            6,
        )
        self.assertEqual(
            first["prior_h002_partition_overlap"]["also_h002_held_out_pages"],
            [],
        )

    def test_eva_analyses_reject_other_alphabets(self) -> None:
        gc = parse_ivtff((ROOT / "data/raw/transcriptions/GC2a-n.txt").read_bytes())
        with self.assertRaises(ValueError):
            baseline_report(gc)


if __name__ == "__main__":
    unittest.main()
