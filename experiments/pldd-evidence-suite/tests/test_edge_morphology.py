from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.analyze_edge_morphology import render_markdown
from voynich.edge_morphology import (
    analyze_edge_morphology,
    split_family_word,
    strict_sta1_family_words,
)
from voynich.ivtff import parse_ivtff


class EdgeMorphologyFixtureTests(unittest.TestCase):
    def test_strict_sta1_words_and_slotting(self) -> None:
        self.assertEqual(
            strict_sta1_family_words(
                "D1A1Q2<->A1G1.<!inert>A1H1.[A1:B1].A1,Z1.?"
            ),
            ("DAQ", "AG", "AH"),
        )
        self.assertEqual(
            split_family_word("DABG", ("D",), ("G", "H")),
            ("D", "AB", "G"),
        )
        self.assertEqual(
            split_family_word("DG", ("D",), ("G", "H")),
            ("D", "G", ""),
        )
        self.assertEqual(
            split_family_word("AG", ("D",), ("G", "H")),
            ("", "A", "G"),
        )


class PinnedEdgeMorphologyPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = analyze_edge_morphology(
            parse_ivtff(
                (ROOT / "data/raw/transcriptions/sta1/ZL3b.txt").read_bytes()
            )
        )

    def test_p001_regression_and_failed_control(self) -> None:
        report = self.report
        self.assertEqual(report["split"]["tag"], "H004-v1")
        self.assertIn("simultaneous scratch", report["protocol_status"])
        self.assertEqual(
            report["selection"]["selected_prefix_families"], ["D"]
        )
        self.assertEqual(
            report["selection"]["selected_suffix_families"], ["G", "H"]
        )
        self.assertEqual(
            report["partitions"],
            {
                "train": {
                    "pages_with_accepted_prose_words": 130,
                    "accepted_tokens": 19031,
                    "family_types": 2822,
                },
                "calibration": {
                    "pages_with_accepted_prose_words": 33,
                    "accepted_tokens": 4150,
                    "family_types": 1085,
                },
                "test": {
                    "pages_with_accepted_prose_words": 44,
                    "accepted_tokens": 6610,
                    "family_types": 1505,
                },
            },
        )
        calibration = report["evaluation"]["calibration"]
        test = report["evaluation"]["test"]
        self.assertEqual(
            (calibration["productive_unseen_types"], calibration["unseen_affixed_types"]),
            (45, 76),
        )
        self.assertEqual(
            (test["productive_unseen_types"], test["unseen_affixed_types"]),
            (69, 123),
        )
        control = report["equal_cardinality_control"]
        self.assertEqual(control["equal_cardinality_inventories"], 5082)
        self.assertEqual(control["selected_inventory_rank_from_best"], 2309)
        self.assertAlmostEqual(control["selected_inventory_percentile"], 0.545848)
        self.assertFalse(control["gate_met"])
        self.assertFalse(report["advancement"]["criterion_met"])
        self.assertIn("assign no gloss", report["advancement"]["disposition"])

    def test_generated_p001_artifacts_are_current(self) -> None:
        checked_json = json.loads(
            (ROOT / "results/p001-edge-morphology.json").read_text()
        )
        checked_markdown = (
            ROOT / "results/p001-edge-morphology.md"
        ).read_text()
        self.assertEqual(checked_json, self.report)
        self.assertEqual(checked_markdown, render_markdown(self.report))


if __name__ == "__main__":
    unittest.main()

