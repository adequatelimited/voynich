from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.ivtff import parse_ivtff
from voynich.plant_anchors import (
    SOURCE_MANIFEST_SHA256,
    StrictQuery,
    bm25_scores,
    build_strict_queries,
    canonical_json_bytes,
    descending_midranks,
    family_ngrams,
    is_holdout_physical_folio,
    physical_folio,
    render_h005_markdown,
    run_h005_zg,
)


def _document(alphabet: str, pages: list[tuple[str, str, str]]) -> object:
    lines = [f"#=IVTFF {alphabet} 2.0 M"]
    for page_id, variables, locus_text in pages:
        lines.append(f"<{page_id}> <! {variables}>")
        lines.extend(locus_text.split("\n"))
    return parse_ivtff(("\n".join(lines) + "\n").encode("ascii"))


class H005PrimitiveTests(unittest.TestCase):
    def test_physical_folio_and_frozen_holdout(self) -> None:
        self.assertEqual(physical_folio("f90r2"), "f90")
        self.assertEqual(physical_folio("f19r"), "f19")
        self.assertTrue(is_holdout_physical_folio("f19"))
        self.assertTrue(is_holdout_physical_folio("f48"))
        self.assertFalse(is_holdout_physical_folio("f96"))

    def test_family_ngrams_are_within_token_and_boundary_marked(self) -> None:
        self.assertEqual(
            family_ngrams("AB"),
            ("^A", "AB", "B$", "^AB", "AB$"),
        )

    def test_bm25_uses_query_multiplicity_and_midranks(self) -> None:
        documents = {
            "f1r": ("A", "A", "B"),
            "f2r": ("A", "C"),
            "f3r": ("C", "C"),
        }
        single = bm25_scores(("A",), documents)
        doubled = bm25_scores(("A", "A"), documents)
        self.assertAlmostEqual(doubled["f1r"], 2 * single["f1r"])
        self.assertGreater(single["f1r"], single["f2r"])
        self.assertEqual(
            descending_midranks({"a": 2.0, "b": 1.0, "c": 1.0}),
            {"a": 1.0, "b": 2.5, "c": 2.5},
        )


class H005QueryGateTests(unittest.TestCase):
    def test_query_gate_is_exact_locus_type_component_and_family(self) -> None:
        eva = _document(
            "Eva-",
            [
                ("f10r", "$I=P $L=A $H=1", "<f10r.1,@Lf> otoldy"),
                ("f1r", "$I=H $L=A $H=1", "<f1r.1,@P0> <%>daiin<$>"),
                ("f2r", "$I=H $L=A $H=1", "<f2r.1,@P0> <%>chedy<$>"),
            ],
        )
        zl = _document(
            "STA1",
            [
                ("f10r", "$I=P $L=A $H=1", "<f10r.1,@Lf> A1B1"),
                ("f1r", "$I=H $L=A $H=1", "<f1r.1,@P0> <%>A1B1<$>"),
                ("f2r", "$I=H $L=A $H=1", "<f2r.1,@P0> <%>C1D1<$>"),
            ],
        )
        gc = _document(
            "STA1",
            [
                ("f10r", "$I=P $L=A $H=1", "<f10r.1,@Lf> A2B2"),
                ("f1r", "$I=H $L=A $H=1", "<f1r.1,@P0> <%>A2B2<$>"),
                ("f2r", "$I=H $L=A $H=1", "<f2r.1,@P0> <%>C2D2<$>"),
            ],
        )
        manifest = {
            "pairs": [
                {
                    "pair_id": "p1",
                    "quire": "q1",
                    "fragment_page": "f10r",
                    "fragment_number": 1,
                    "target_page": "f1r",
                    "strength": "S",
                    "label_loci": ["f10r.1"],
                    "mapping_status": "lf_locus",
                }
            ]
        }
        queries, audits, _ = build_strict_queries(manifest, eva, zl, gc)
        self.assertEqual(len(queries), 1)
        self.assertEqual(queries[0].query_families, ("AB",))
        self.assertTrue(audits[0].admitted)

        row_order_manifest = {
            "pairs": [
                {
                    **manifest["pairs"][0],
                    "pair_id": "p-row-order",
                    "mapping_status": "lf_mapping_by_row_order",
                }
            ]
        }
        queries, audits, _ = build_strict_queries(
            row_order_manifest, eva, zl, gc
        )
        self.assertEqual(queries, ())
        self.assertIn("lf_mapping_by_row_order", audits[0].reasons)

        bad_gc = _document(
            "STA1",
            [
                ("f10r", "$I=P $L=A $H=1", "<f10r.1,@Lf> A2C2"),
                ("f1r", "$I=H $L=A $H=1", "<f1r.1,@P0> <%>A2B2<$>"),
                ("f2r", "$I=H $L=A $H=1", "<f2r.1,@P0> <%>C2D2<$>"),
            ],
        )
        queries, audits, _ = build_strict_queries(manifest, eva, zl, bad_gc)
        self.assertEqual(queries, ())
        self.assertIn("zl_gc_family_disagreement:f10r.1", audits[0].reasons)

    def test_small_null_run_is_deterministic_and_selection_adjusted(self) -> None:
        pages = ("f1r", "f2r", "f3r", "f4r")
        tokens = {
            "f1r": ("A", "A"),
            "f2r": ("B", "B"),
            "f3r": ("C", "C"),
            "f4r": ("D", "D"),
        }
        queries = (
            StrictQuery(
                "d", "q15", "f10r", 1, "f1r", "f1", "M",
                ("f10r.1",), ("A",), ("A", "1"), "discovery", pages,
            ),
            StrictQuery(
                "h", "q15", "f11r", 2, "f2r", "f2", "M",
                ("f11r.1",), ("B",), ("A", "1"), "holdout", pages,
            ),
        )
        corpus = {
            ("A", "1"): {
                "candidate_pages": pages,
                "zl_tokens": tokens,
                "gc_tokens": tokens,
            }
        }
        first = run_h005_zg(queries, corpus, permutations=7, seed=5)
        second = run_h005_zg(queries, corpus, permutations=7, seed=5)
        self.assertEqual(first, second)
        self.assertEqual(first["model_selection"]["selected_model"], "M0")
        self.assertEqual(sum(first["null_selected_model_counts"].values()), 7)


class H005PinnedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest_path = ROOT / "data/derived/h005-source-anchor-manifest.json"
        cls.manifest_bytes = cls.manifest_path.read_bytes()
        cls.manifest = json.loads(cls.manifest_bytes)
        cls.eva = parse_ivtff(
            (ROOT / "data/raw/transcriptions/ZL3b-n.txt").read_bytes()
        )
        cls.zl = parse_ivtff(
            (ROOT / "data/raw/transcriptions/sta1/ZL3b.txt").read_bytes()
        )
        cls.gc = parse_ivtff(
            (ROOT / "data/raw/transcriptions/sta1/GC2a_0.txt").read_bytes()
        )

    def test_frozen_manifest_hash_and_complete_claim_count(self) -> None:
        self.assertEqual(sha256(self.manifest_bytes).hexdigest(), SOURCE_MANIFEST_SHA256)
        self.assertEqual(len(self.manifest["pairs"]), 35)
        self.assertEqual(len({pair["pair_id"] for pair in self.manifest["pairs"]}), 35)

    def test_strict_query_inventory_and_physical_holdout_are_frozen(self) -> None:
        queries, audits, _ = build_strict_queries(
            self.manifest, self.eva, self.zl, self.gc
        )
        self.assertEqual(len(audits), 35)
        self.assertEqual(len(queries), 17)
        self.assertNotIn(
            "q15-f89r2-40-f87v", {query.pair_id for query in queries}
        )
        self.assertEqual(
            {query.pair_id for query in queries if query.split == "holdout"},
            {
                "q19-f102v1-240-f19r",
                "q15-f89r1-26-f43v",
                "q19-f99v-95-f44r",
                "q15-f89v2-54-f48v",
                "q15-f89r1-25-f57r",
            },
        )
        self.assertEqual(
            {query.target_physical_folio for query in queries if query.split == "holdout"},
            {"f19", "f43", "f44", "f48", "f57"},
        )

    def test_production_artifacts_are_canonical_and_pre_it(self) -> None:
        json_path = ROOT / "results/h005-plant-anchors.json"
        markdown_path = ROOT / "results/h005-plant-anchors.md"
        sidecar_path = ROOT / "results/h005-plant-anchors.sha256.txt"
        report_bytes = json_path.read_bytes()
        report_hash = sha256(report_bytes).hexdigest()
        report = json.loads(report_bytes)
        self.assertEqual(report_bytes, canonical_json_bytes(report))
        self.assertEqual(
            sidecar_path.read_text(encoding="ascii"),
            f"{report_hash}  {json_path.name}\n",
        )
        self.assertEqual(
            markdown_path.read_text(encoding="utf-8"),
            render_h005_markdown(report, report_hash),
        )
        self.assertEqual(report["zg_analysis"]["permutations_run"], 9_999)
        self.assertEqual(
            report["manifest_audit"]["raw_holdout_claims_before_query_gates"],
            7,
        )
        self.assertEqual(
            report["manifest_audit"][
                "raw_holdout_physical_folios_before_query_gates"
            ],
            ["f19", "f4", "f43", "f44", "f48", "f57"],
        )
        holdout_metrics = report["zg_analysis"]["holdout_metrics"]
        self.assertEqual(
            set(holdout_metrics["by_source_strength_holdout_conservative_mrr"]),
            {"M", "P", "S"},
        )
        self.assertEqual(
            set(holdout_metrics["by_unique_query_form_holdout_conservative_mrr"]),
            {"ACACKABAG", "AQABBA", "BACABABA", "KAQAB"},
        )
        reserved_it = report["inputs"]["reserved_it_sta1"]
        self.assertFalse(reserved_it["opened_by_this_analysis"])
        self.assertFalse(reserved_it["parsed_by_this_analysis"])
        self.assertFalse(reserved_it["target_prose_projected_by_this_analysis"])


if __name__ == "__main__":
    unittest.main()
