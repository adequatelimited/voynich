"""Scientific validity tests exercise assumptions and conserved quantities, not UI details."""
import collections
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/research"))
from engine import digest, information, known_plaintext, meaningful_text, nmi, normalize, parse_ivtff, shuffled_tokens, synthetic


class ParserTests(unittest.TestCase):
    def parse_fixture(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.txt"
            path.write_text(text, encoding="ascii")
            return parse_ivtff(path)

    def test_uncertainty_policies_and_atomic_rare_symbols(self):
        raw = "<%>ab,cd.ef[gh:ij].k?l.{cth}@194;<!uncertain>.x<->y<$>"
        join, stats = normalize(raw, "join")
        split, _ = normalize(raw, "split")
        strict, _ = normalize(raw, "strict")
        self.assertEqual(join, [list("abcd"), list("efgh"), ["c", "t", "h", "@194;"], ["x"], ["y"]])
        self.assertEqual(split[:2], [list("ab"), list("cd")])
        self.assertEqual(strict, [["c", "t", "h", "@194;"], ["x"], ["y"]])
        self.assertEqual(stats["excluded_tokens"], 1)
        self.assertEqual(stats["drawing_breaks"], 1)

    def test_foldout_identity_and_tag_scope(self):
        parsed = self.parse_fixture("#=IVTFF Eva- 2.0 M 5\n<f85r2> <! $H=@ $I=C>\n<f85r2.1,@P0> <@H=2>abc\n<f85r2.2,+P0> def\n<fRos> <! $H=1 $I=C>\n<fRos.1,@L0> ghi\n")
        self.assertEqual([x["page"] for x in parsed["loci"]], ["f85r2", "f85r2", "fRos"])
        self.assertEqual([x["variables"]["H"] for x in parsed["loci"]], ["2", "2", "1"])

    def test_continuations(self):
        parsed = self.parse_fixture("#=IVTFF Eva- 2.0 M 5\n<f1r> <! $I=H>\n<f1r.1,@P0> abc./\n/def\n")
        self.assertEqual(parsed["loci"][0]["raw"], "abc.def")

    def test_missing_page_and_duplicates_fail(self):
        for data in ("<f1r.1,@P0> abc", "<f1r> <! $I=H>\n<f2r.1,@P0> abc", "<f1r> <! $I=H>\n<f1r.1,@P0> abc\n<f1r.1,+P0> def"):
            with self.assertRaises(ValueError):
                self.parse_fixture("#=IVTFF Eva- 2.0 M 5\n" + data)

    def test_pinned_actual_corpus_counts(self):
        for name, sid, loci, pages in (("ZL3b-n.txt", "zl3b", 5385, 227), ("GC2a-n.txt", "gc2a", 5367, 226)):
            path = ROOT / "data/corpora" / name
            manifest = json.loads((ROOT / f"data/manifests/{sid}.json").read_text())
            parsed = parse_ivtff(path)
            self.assertEqual(parsed["sha256"], manifest["sha256"])
            self.assertEqual(len(parsed["loci"]), loci)
            self.assertEqual(len(parsed["pages"]), pages)


class MetricTests(unittest.TestCase):
    def test_conditional_entropy_known_sequences(self):
        tokens = [list("ababab"), list("ababab")]
        metrics = information(tokens)
        self.assertAlmostEqual(metrics["unigram_bits"], 1)
        self.assertAlmostEqual(metrics["next_symbol_given_previous_bits"], 0)
        self.assertEqual(metrics["bigrams"], 10)

    def test_shuffle_preserves_lengths_and_symbol_multiset(self):
        tokens = known_plaintext(100)
        shuffled = shuffled_tokens(tokens, random.Random(408))
        self.assertEqual(list(map(len, tokens)), list(map(len, shuffled)))
        self.assertEqual(collections.Counter(s for t in tokens for s in t), collections.Counter(s for t in shuffled for s in t))
        self.assertNotEqual(tokens, shuffled)
        self.assertEqual(shuffled, shuffled_tokens(tokens, random.Random(408)))

    def test_generator_is_bounded_deterministic_and_not_manuscript(self):
        tokens = known_plaintext(1000)
        first = synthetic(tokens, random.Random(408))
        self.assertEqual(first, synthetic(tokens, random.Random(408)))
        self.assertEqual(len(first), 1000)
        self.assertTrue(all(1 <= len(t) <= 12 for t in first))
        self.assertNotEqual(first, tokens)

    def test_nmi_invariant_to_label_names(self):
        self.assertAlmostEqual(nmi([0,0,1,1], ["A","A","B","B"]), 1)
        self.assertAlmostEqual(nmi([0,0,1,1], ["A","B","A","B"]), 0)

    def test_meaningful_comparison_removes_license_wrapper(self):
        tokens = meaningful_text(ROOT / "data/corpora/pg11.txt")
        self.assertGreater(len(tokens), 20000)
        self.assertNotIn(list("gutenberg"), tokens)


if __name__ == "__main__":
    unittest.main()
