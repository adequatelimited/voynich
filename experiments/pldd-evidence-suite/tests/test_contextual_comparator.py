from __future__ import annotations

from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.contextual_comparator import (
    BOS1,
    BOS2,
    ExactWeightInfeasibleError,
    UNK,
    _event_bits,
    _metric_comparison,
    _nearest_rank,
    _seed_for_order,
    build_target_bases,
    build_target_distributions,
    fractions_to_integer_weights,
    render_h004b2_markdown,
    simulate_teacher_forced,
    summarize_analytic,
    train_probability_model,
    run_h004b2_contextual_comparator,
)
from voynich.local_order import LocalOrderPage, Target


def training_page(page_id: str, currier: str, tokens: tuple[str, ...]) -> LocalOrderPage:
    stratum = ("H", currier, "1")
    cell = (stratum, 2, False, "middle")
    return LocalOrderPage(
        page_id=page_id,
        tokens=tokens,
        cells=((cell, tuple(range(len(tokens)))),),
        targets=(),
        runs=(tuple(range(len(tokens))),),
    )


def target_page(page_id: str, currier: str) -> LocalOrderPage:
    stratum = ("H", currier, "1")
    context = ("aa", "ab") * 5
    tokens = context + ("aa", "ab")
    context_cell = (stratum, 2, False, "middle")
    target_cell = (stratum, 2, False, "last")
    return LocalOrderPage(
        page_id=page_id,
        tokens=tokens,
        cells=((context_cell, tuple(range(10))), (target_cell, (10, 11))),
        targets=(Target(10, tuple(range(10)), stratum),),
        runs=(tuple(range(12)),),
    )


class ContextualComparatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.training = (
            training_page("f1r", "A", ("aa", "aa", "ab", "aa", "ac")),
            training_page("f2r", "B", ("aa", "ab", "aa", "ab", "ad")),
        )

    def test_singletons_map_to_UNK_and_unseen_context_backs_off_exactly(self) -> None:
        model = train_probability_model(self.training)
        self.assertEqual(model.vocabularies["A"], frozenset({"aa", UNK}))
        self.assertEqual(model.unigrams["A"], Counter({"aa": 3, UNK: 2}))
        self.assertEqual(
            sum(model.p0("A", token) for token in model.vocabularies["A"]),
            1,
        )
        self.assertEqual(model.p1("A", "unseen", "aa"), model.p0("A", "aa"))
        self.assertEqual(
            model.p2("A", "also-unseen", "unseen", "aa"),
            model.p1("A", "unseen", "aa"),
        )
        self.assertGreater(model.context1_count("A", BOS1), 0)
        self.assertGreater(model.context2_count("A", BOS2, BOS1), 0)

    def test_fraction_weights_are_exact_and_reduced(self) -> None:
        cumulative, total = fractions_to_integer_weights(
            (Fraction(1, 6), Fraction(1, 3), Fraction(1, 2))
        )
        self.assertEqual(cumulative, (1, 3, 6))
        self.assertEqual(total, 6)

    def test_fraction_weights_fail_closed_above_frozen_ceiling(self) -> None:
        denominator = 1 << 4096
        with self.assertRaisesRegex(ExactWeightInfeasibleError, "4096 bits"):
            fractions_to_integer_weights(
                (
                    Fraction(1, denominator),
                    Fraction(denominator - 1, denominator),
                )
            )

    def test_event_semantics_and_frozen_seed(self) -> None:
        context = ("aa", "bb")
        self.assertEqual(_event_bits("aa", context), 0b101)
        self.assertEqual(_event_bits("ab", context), 0b011)
        self.assertEqual(_event_bits("cccc", context), 0)
        expected_seed = int.from_bytes(
            sha256(
                b"H004-B-v2|teacher-forced|order=2|seed=4004"
            ).digest()[:16],
            "big",
        )
        self.assertEqual(_seed_for_order(2, 4004), expected_seed)

    def test_quantile_tail_ties_and_unrounded_gate(self) -> None:
        self.assertEqual(_nearest_rank(tuple(range(1, 10000)), 0.01), 100)
        self.assertEqual(_nearest_rank(tuple(range(1, 10000)), 0.05), 500)
        report = _metric_comparison(
            0.5,
            0.47,
            [0.5, 0.4, 0.5],
            [0.5, 0.5],
            [0.47, 0.47],
            primary=True,
        )
        self.assertEqual(report["conditional_tail_area"], 0.75)
        self.assertTrue(report["advancement_checks"]["delta_at_least_0_02"])

    def test_top_level_rejects_nonfrozen_simulation_parameters_first(self) -> None:
        with self.assertRaisesRegex(ValueError, "frozen at 9999"):
            run_h004b2_contextual_comparator(  # type: ignore[arg-type]
                None,
                {},
                h004a_report_sha256="unused",
                replicates=19,
                master_seed=4004,
            )

    def test_production_artifacts_are_pinned_and_renderer_current(self) -> None:
        json_path = ROOT / "results/h004b2-contextual-comparator.json"
        markdown_path = ROOT / "results/h004b2-contextual-comparator.md"
        raw = json_path.read_bytes()
        report = json.loads(raw)
        self.assertEqual(
            sha256(raw).hexdigest(),
            "01d26e78676f938e010c1d21fd2ce627bf9192932c4dee2fe2bd21a078c381bf",
        )
        self.assertEqual(report["analysis_version"], "H004-B-v2")
        self.assertEqual(report["protocol"]["replicates_per_order"], 9999)
        self.assertEqual(report["protocol"]["master_seed"], 4004)
        self.assertFalse(report["both_comparators_valid"])
        self.assertFalse(report["advancement_gate_met"])
        self.assertFalse(report["H004_CU_discriminating_evidence_rejected"])
        self.assertEqual(
            report["disposition"],
            "inconclusive: both contextual comparators failed validity",
        )
        self.assertEqual(
            markdown_path.read_text(encoding="utf-8"),
            render_h004b2_markdown(report),
        )

    def test_q_times_likelihood_ratio_and_simulation_are_deterministic(self) -> None:
        model = train_probability_model(self.training)
        pages = (target_page("f3r", "A"), target_page("f4r", "B"))
        bases = build_target_bases(pages, model)
        for order in (1, 2):
            distributions = build_target_distributions(bases, model, order=order)
            for distribution in distributions:
                self.assertEqual(sum(distribution.probabilities, Fraction()), 1)
                expected_raw = tuple(
                    q
                    * (
                        model.p1(
                            distribution.base.currier,
                            distribution.base.mapped_history1,
                            mapped,
                        )
                        if order == 1
                        else model.p2(
                            distribution.base.currier,
                            distribution.base.mapped_history2,
                            distribution.base.mapped_history1,
                            mapped,
                        )
                    )
                    / model.p0(distribution.base.currier, mapped)
                    for q, mapped in zip(
                        distribution.base.q, distribution.base.mapped_candidates
                    )
                )
                normalizer = sum(expected_raw, Fraction())
                self.assertEqual(
                    distribution.probabilities,
                    tuple(value / normalizer for value in expected_raw),
                )

        distributions = build_target_distributions(bases, model, order=2)
        analytic = summarize_analytic(distributions, page_count=2)
        first = simulate_teacher_forced(
            distributions, analytic, order=2, replicates=19, master_seed=4004
        )
        second = simulate_teacher_forced(
            distributions, analytic, order=2, replicates=19, master_seed=4004
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first.overall[0]), 19)


if __name__ == "__main__":
    unittest.main()
