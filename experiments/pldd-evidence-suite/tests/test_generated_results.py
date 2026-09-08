from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.analyze_corpus import render_markdown
from voynich.analysis import baseline_report
from voynich.ivtff import parse_ivtff


class GeneratedResultFreshnessTests(unittest.TestCase):
    def test_baseline_artifacts_match_current_analysis(self) -> None:
        report = baseline_report(
            parse_ivtff((ROOT / "data/raw/transcriptions/ZL3b-n.txt").read_bytes()),
            zl_sta_document=parse_ivtff(
                (ROOT / "data/raw/transcriptions/sta1/ZL3b.txt").read_bytes()
            ),
            gc_sta_document=parse_ivtff(
                (ROOT / "data/raw/transcriptions/sta1/GC2a_0.txt").read_bytes()
            ),
        )

        checked_json = json.loads((ROOT / "results/baseline-zl3b.json").read_text())
        checked_markdown = (ROOT / "results/baseline-zl3b.md").read_text()
        self.assertEqual(checked_json, report)
        self.assertEqual(checked_markdown, render_markdown(report))


if __name__ == "__main__":
    unittest.main()
