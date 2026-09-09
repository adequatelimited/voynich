from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.ivtff import parse_ivtff
from voynich.local_order import (
    build_local_order_pages,
    edit_distance_class,
    render_h004_markdown,
    run_h004_local_order,
)


class LocalOrderTests(unittest.TestCase):
    def test_edit_distance_is_capped_and_symmetric(self) -> None:
        cases = [
            ("daiin", "daiin", 0),
            ("daiin", "dainn", 1),
            ("daiin", "dain", 1),
            ("dain", "daiin", 1),
            ("daiin", "qokedy", 2),
        ]
        for left, right, expected in cases:
            self.assertEqual(edit_distance_class(left, right), expected)
            self.assertEqual(edit_distance_class(right, left), expected)

    def test_uncertainty_resets_the_causal_window(self) -> None:
        raw = (
            b"#=IVTFF Eva- 2.0 M\n"
            b"<f1r> <! $I=H $L=A $H=1>\n"
            b"<f1r.1,@P0> <%>daiin.chol.qokedy.daiin,chedy.chol.shol.daiin<$>\n"
        )
        pages = build_local_order_pages(parse_ivtff(raw), window=2)
        self.assertEqual(len(pages), 1)
        self.assertEqual(len(pages[0].targets), 2)
        self.assertEqual(pages[0].runs, ((0, 1, 2), (3, 4, 5)))
        self.assertEqual(
            tuple(pages[0].tokens[index] for index in pages[0].targets[-1].context),
            ("chol", "shol"),
        )

    def test_pinned_inventory_and_small_run_are_deterministic(self) -> None:
        document = parse_ivtff(
            (ROOT / "data/raw/transcriptions/ZL3b-n.txt").read_bytes()
        )
        first = run_h004_local_order(document, permutations=3)
        second = run_h004_local_order(document, permutations=3)
        self.assertEqual(first, second)
        self.assertEqual(first["input"]["source_sha256"], "bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc")
        self.assertEqual(first["eligibility"]["eligible_reserved_pages"], 33)
        self.assertEqual(first["eligibility"]["reserved_targets"], 2072)
        self.assertFalse(first["mechanism_gate"]["copy_edit_mechanism_advanced"])

    def test_pinned_production_artifacts_are_internally_current(self) -> None:
        report = json.loads(
            (ROOT / "results/h004-local-order.json").read_text(encoding="utf-8")
        )
        markdown = (ROOT / "results/h004-local-order.md").read_text(encoding="utf-8")

        self.assertEqual(report["analysis_version"], "H004-v1")
        self.assertEqual(report["protocol"]["permutations"], 9999)
        self.assertEqual(report["protocol"]["seed"], 4004)
        self.assertTrue(report["static_matched_null_gate_met"])
        self.assertEqual(report["eligibility"]["movable_reserved_targets"], 2000)
        self.assertEqual(
            report["held_out_static_null"]["copy_or_one_edit"]["delta"],
            0.050445,
        )
        self.assertEqual(
            report["held_out_static_null"]["one_edit_without_exact"][
                "monte_carlo_p"
            ],
            0.0003,
        )
        self.assertEqual(markdown, render_h004_markdown(report))


if __name__ == "__main__":
    unittest.main()
