"""Frozen H004-B-v2 teacher-forced contextual comparator.

The comparator reweights each reserved target's observed page/layout-cell
distribution with discovery-trained order-1 or order-2 transition likelihood
ratios.  Histories remain observed and fixed.  This is not a free-running
Markov generator and makes no semantic claim.
"""

from __future__ import annotations

from bisect import bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import accumulate
import math
import random
import statistics
from typing import Any, Callable, Iterable, Sequence

from .ivtff import Document
from .local_order import CellKey, LocalOrderPage, Target, build_local_order_pages, edit_distance_class


VERSION = "H004-B-v2"
PINNED_ZL3B_SHA256 = "bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc"
PINNED_H004A_REPORT_SHA256 = "53caf3b04298838e102ddf4ac169a756e471b965de42abb8452b725ff042e469"
FROZEN_REPLICATES = 9999
FROZEN_MASTER_SEED = 4004
# Exact draws wider than 4096 bits could require more than 20 GB of PRNG
# output across the frozen 41,435,856 target draws and are not operationally
# practical here.  Fail closed instead of approximating rational weights.
MAX_EXACT_WEIGHT_BITS = 4096
UNK = "<UNK>"
BOS2 = "<BOS2>"
BOS1 = "<BOS1>"
METRIC_NAMES = ("C_copy_or_one_edit", "U_one_edit_without_exact", "exact_repeat_diagnostic")


def is_reserved_page(page_id: str) -> bool:
    return sha256(f"H004-v1:{page_id}".encode("ascii")).digest()[0] < 51


class ProbabilityModel:
    """Exact hierarchical unigram, bigram, and trigram probabilities."""

    def __init__(
        self,
        *,
        surface_counts: dict[str, Counter[str]],
        mapped_unigrams: dict[str, Counter[str]],
        order1: dict[str, dict[str, Counter[str]]],
        order2: dict[str, dict[tuple[str, str], Counter[str]]],
        vocabularies: dict[str, frozenset[str]],
    ) -> None:
        self.surface_counts = surface_counts
        self.unigrams = mapped_unigrams
        self.order1 = order1
        self.order2 = order2
        self.vocabularies = vocabularies
        self.totals = {key: sum(counts.values()) for key, counts in mapped_unigrams.items()}
        self._p1_cache: dict[tuple[str, str, str], Fraction] = {}
        self._p2_cache: dict[tuple[str, str, str, str], Fraction] = {}

    def phi(self, currier: str, token: str) -> str:
        return token if token in self.vocabularies[currier] else UNK

    def p0(self, currier: str, output: str) -> Fraction:
        if output not in self.vocabularies[currier]:
            raise ValueError(f"output {output!r} is outside mapped vocabulary {currier}")
        count = self.unigrams[currier][output]
        return Fraction(2 * count + 1, 2 * self.totals[currier] + len(self.vocabularies[currier]))

    def context1_count(self, currier: str, history: str) -> int:
        return sum(self.order1[currier].get(history, {}).values())

    def context2_count(self, currier: str, history2: str, history1: str) -> int:
        return sum(self.order2[currier].get((history2, history1), {}).values())

    def p1(self, currier: str, history: str, output: str) -> Fraction:
        key = (currier, history, output)
        cached = self._p1_cache.get(key)
        if cached is not None:
            return cached
        transitions = self.order1[currier].get(history, Counter())
        probability = (Fraction(transitions[output]) + self.p0(currier, output)) / (
            sum(transitions.values()) + 1
        )
        self._p1_cache[key] = probability
        return probability

    def p2(
        self, currier: str, history2: str, history1: str, output: str
    ) -> Fraction:
        key = (currier, history2, history1, output)
        cached = self._p2_cache.get(key)
        if cached is not None:
            return cached
        transitions = self.order2[currier].get((history2, history1), Counter())
        probability = (
            Fraction(transitions[output]) + self.p1(currier, history1, output)
        ) / (sum(transitions.values()) + 1)
        self._p2_cache[key] = probability
        return probability


class ExactWeightInfeasibleError(RuntimeError):
    """Exact rational sampling exceeded the frozen operational ceiling."""


def train_probability_model(pages: Iterable[LocalOrderPage]) -> ProbabilityModel:
    """Train the frozen singleton-to-UNK model from discovery runs."""

    pages = tuple(pages)
    surface_counts: dict[str, Counter[str]] = {"A": Counter(), "B": Counter()}
    cell_by_page = {page.page_id: _cell_by_position(page) for page in pages}
    for page in pages:
        cells = cell_by_page[page.page_id]
        for run in page.runs:
            if not run:
                continue
            currier = cells[run[0]][0][1]
            if currier not in ("A", "B"):
                continue
            if any(cells[position][0][1] != currier for position in run):
                raise ValueError("run crosses Currier varieties")
            surface_counts[currier].update(page.tokens[position] for position in run)

    vocabularies = {
        currier: frozenset(
            {token for token, count in counts.items() if count >= 2} | {UNK}
        )
        for currier, counts in surface_counts.items()
    }
    unigrams: dict[str, Counter[str]] = {"A": Counter(), "B": Counter()}
    order1: dict[str, dict[str, Counter[str]]] = {
        "A": defaultdict(Counter),
        "B": defaultdict(Counter),
    }
    order2: dict[str, dict[tuple[str, str], Counter[str]]] = {
        "A": defaultdict(Counter),
        "B": defaultdict(Counter),
    }

    for page in pages:
        cells = cell_by_page[page.page_id]
        for run in page.runs:
            if not run:
                continue
            currier = cells[run[0]][0][1]
            if currier not in ("A", "B"):
                continue
            history2, history1 = BOS2, BOS1
            for position in run:
                surface = page.tokens[position]
                output = surface if surface in vocabularies[currier] else UNK
                unigrams[currier][output] += 1
                order1[currier][history1][output] += 1
                order2[currier][(history2, history1)][output] += 1
                history2, history1 = history1, output

    for currier in ("A", "B"):
        if not unigrams[currier]:
            raise ValueError(f"no discovery training tokens for Currier {currier}")
        if set(unigrams[currier]) - vocabularies[currier]:
            raise AssertionError("mapped output escaped vocabulary")
    return ProbabilityModel(
        surface_counts=surface_counts,
        mapped_unigrams=unigrams,
        order1=order1,
        order2=order2,
        vocabularies=vocabularies,
    )


def _cell_by_position(page: LocalOrderPage) -> tuple[CellKey, ...]:
    cells: list[CellKey | None] = [None] * len(page.tokens)
    for key, positions in page.cells:
        for position in positions:
            if cells[position] is not None:
                raise AssertionError("position belongs to multiple H004 cells")
            cells[position] = key
    if any(cell is None for cell in cells):
        raise AssertionError("position is missing an H004 cell")
    return tuple(cell for cell in cells if cell is not None)


def fractions_to_integer_weights(
    probabilities: Sequence[Fraction],
    *,
    maximum_bits: int = MAX_EXACT_WEIGHT_BITS,
) -> tuple[tuple[int, ...], int]:
    """Convert normalized rational probabilities to reduced exact cumulative weights."""

    if not probabilities or any(value <= 0 for value in probabilities):
        raise ValueError("candidate probabilities must be nonempty and positive")
    if sum(probabilities, Fraction()) != 1:
        raise ValueError("candidate probabilities must sum exactly to one")
    common = 1
    for probability in probabilities:
        common = math.lcm(common, probability.denominator)
        if common.bit_length() > maximum_bits:
            raise ExactWeightInfeasibleError(
                f"exact common denominator exceeds {maximum_bits} bits; "
                "no approximate fallback is permitted"
            )
    weights = [value.numerator * (common // value.denominator) for value in probabilities]
    divisor = math.gcd(*weights)
    weights = [value // divisor for value in weights]
    total = sum(weights)
    if total.bit_length() > maximum_bits:
        raise ExactWeightInfeasibleError(
            f"exact total weight exceeds {maximum_bits} bits; "
            "no approximate fallback is permitted"
        )
    if any(Fraction(weight, total) != probability for weight, probability in zip(weights, probabilities)):
        raise AssertionError("integer weights do not reproduce exact probabilities")
    return tuple(accumulate(weights)), total


def _event_bits(candidate: str, context: tuple[str, ...]) -> int:
    if candidate in context:
        return 0b101  # C and exact
    if any(edit_distance_class(candidate, token) == 1 for token in context):
        return 0b011  # C and U
    return 0


def _log_fraction(value: Fraction) -> float:
    return math.log(value.numerator) - math.log(value.denominator)


@dataclass(frozen=True)
class TargetBase:
    page_index: int
    page_id: str
    currier: str
    target: Target
    actual: str
    context: tuple[str, ...]
    candidates: tuple[str, ...]
    q: tuple[Fraction, ...]
    mapped_candidates: tuple[str, ...]
    mapped_history2: str
    mapped_history1: str
    event_bits: tuple[int, ...]
    actual_event_bits: int
    actual_candidate_index: int
    distinct_cell: bool
    baseline_unk_mass: Fraction


@dataclass(frozen=True)
class TargetDistribution:
    base: TargetBase
    order: int
    probabilities: tuple[Fraction, ...]
    cumulative_weights: tuple[int, ...]
    total_weight: int
    expected_events: tuple[Fraction, Fraction, Fraction]
    reweighted_unk_mass: Fraction
    actual_log_lift: float
    context_supported: bool


def build_target_bases(
    pages: tuple[LocalOrderPage, ...], model: ProbabilityModel
) -> tuple[TargetBase, ...]:
    bases: list[TargetBase] = []
    for page_index, page in enumerate(pages):
        cells = _cell_by_position(page)
        cell_counts = {
            key: Counter(page.tokens[position] for position in positions)
            for key, positions in page.cells
        }
        run_by_position: dict[int, tuple[tuple[int, ...], int]] = {}
        for run in page.runs:
            for index, position in enumerate(run):
                if position in run_by_position:
                    raise AssertionError("position occurs in multiple runs")
                run_by_position[position] = (run, index)
        for target in page.targets:
            run, run_index = run_by_position[target.position]
            if run_index < 10 or tuple(run[run_index - 10 : run_index]) != target.context:
                raise AssertionError("target context does not match H004 run skeleton")
            cell = cells[target.position]
            currier = cell[0][1]
            if currier not in ("A", "B") or target.stratum != cell[0]:
                raise AssertionError("target stratum mismatch")
            counts = cell_counts[cell]
            candidates = tuple(sorted(counts))
            cell_size = sum(counts.values())
            q = tuple(Fraction(counts[word], cell_size) for word in candidates)
            context = tuple(page.tokens[position] for position in target.context)
            mapped_candidates = tuple(model.phi(currier, word) for word in candidates)
            mapped_history2 = model.phi(currier, context[-2])
            mapped_history1 = model.phi(currier, context[-1])
            events = tuple(_event_bits(word, context) for word in candidates)
            actual = page.tokens[target.position]
            actual_index = candidates.index(actual)
            unk_mass = sum(
                probability
                for probability, mapped in zip(q, mapped_candidates)
                if mapped == UNK
            )
            bases.append(
                TargetBase(
                    page_index=page_index,
                    page_id=page.page_id,
                    currier=currier,
                    target=target,
                    actual=actual,
                    context=context,
                    candidates=candidates,
                    q=q,
                    mapped_candidates=mapped_candidates,
                    mapped_history2=mapped_history2,
                    mapped_history1=mapped_history1,
                    event_bits=events,
                    actual_event_bits=events[actual_index],
                    actual_candidate_index=actual_index,
                    distinct_cell=len(candidates) >= 2,
                    baseline_unk_mass=unk_mass,
                )
            )
    return tuple(bases)


def build_target_distributions(
    bases: tuple[TargetBase, ...], model: ProbabilityModel, *, order: int
) -> tuple[TargetDistribution, ...]:
    if order not in (1, 2):
        raise ValueError("order must be 1 or 2")
    result: list[TargetDistribution] = []
    for base in bases:
        lifts: list[Fraction] = []
        for mapped in base.mapped_candidates:
            baseline = model.p0(base.currier, mapped)
            contextual = (
                model.p1(base.currier, base.mapped_history1, mapped)
                if order == 1
                else model.p2(
                    base.currier,
                    base.mapped_history2,
                    base.mapped_history1,
                    mapped,
                )
            )
            lifts.append(contextual / baseline)
        raw = tuple(q * lift for q, lift in zip(base.q, lifts))
        normalizer = sum(raw, Fraction())
        probabilities = tuple(value / normalizer for value in raw)
        if any(value <= 0 for value in probabilities) or sum(probabilities, Fraction()) != 1:
            raise AssertionError("invalid contextual target distribution")
        cumulative, total = fractions_to_integer_weights(probabilities)
        expected = tuple(
            sum(
                probability
                for probability, bits in zip(probabilities, base.event_bits)
                if bits & (1 << metric)
            )
            for metric in range(3)
        )
        reweighted_unk = sum(
            probability
            for probability, mapped in zip(probabilities, base.mapped_candidates)
            if mapped == UNK
        )
        actual_probability = probabilities[base.actual_candidate_index]
        actual_q = base.q[base.actual_candidate_index]
        context_supported = (
            model.context1_count(base.currier, base.mapped_history1) > 0
            if order == 1
            else model.context2_count(
                base.currier, base.mapped_history2, base.mapped_history1
            )
            > 0
        )
        result.append(
            TargetDistribution(
                base=base,
                order=order,
                probabilities=probabilities,
                cumulative_weights=cumulative,
                total_weight=total,
                expected_events=expected,
                reweighted_unk_mass=reweighted_unk,
                actual_log_lift=_log_fraction(actual_probability / actual_q),
                context_supported=context_supported,
            )
        )
    return tuple(result)


def _nearest_rank(values: Sequence[float], quantile: float) -> float:
    if not values or not 0 < quantile <= 1:
        raise ValueError("nearest-rank quantile requires data and 0 < q <= 1")
    ordered = sorted(values)
    return ordered[math.ceil(quantile * len(ordered)) - 1]


def _seed_for_order(order: int, master_seed: int) -> int:
    material = f"{VERSION}|teacher-forced|order={order}|seed={master_seed}"
    return int.from_bytes(sha256(material.encode("ascii")).digest()[:16], "big")


def _bits_to_counts(bits: int) -> tuple[int, int, int]:
    return tuple(int(bool(bits & (1 << metric))) for metric in range(3))


@dataclass(frozen=True)
class AnalyticSummary:
    observed_page: tuple[tuple[float, float, float], ...]
    expected_page: tuple[tuple[float, float, float], ...]
    observed_overall: tuple[float, float, float]
    expected_overall: tuple[float, float, float]
    observed_currier: dict[str, tuple[float, float, float]]
    expected_currier: dict[str, tuple[float, float, float]]
    currier_page_observed: dict[
        str, tuple[tuple[float, float, float] | None, ...]
    ]
    currier_page_expected: dict[
        str, tuple[tuple[float, float, float] | None, ...]
    ]
    page_target_counts: tuple[int, ...]
    currier_target_counts: dict[str, int]


def summarize_analytic(
    distributions: tuple[TargetDistribution, ...], *, page_count: int
) -> AnalyticSummary:
    page_observed = [[[0, 0, 0], 0] for _ in range(page_count)]
    page_expected = [[[Fraction(), Fraction(), Fraction()], 0] for _ in range(page_count)]
    currier_observed = {"A": [0, 0, 0, 0], "B": [0, 0, 0, 0]}
    currier_expected = {
        "A": [Fraction(), Fraction(), Fraction(), 0],
        "B": [Fraction(), Fraction(), Fraction(), 0],
    }
    currier_page_observed = {
        "A": [[[0, 0, 0], 0] for _ in range(page_count)],
        "B": [[[0, 0, 0], 0] for _ in range(page_count)],
    }
    currier_page_expected = {
        "A": [[[Fraction(), Fraction(), Fraction()], 0] for _ in range(page_count)],
        "B": [[[Fraction(), Fraction(), Fraction()], 0] for _ in range(page_count)],
    }
    for distribution in distributions:
        page = distribution.base.page_index
        currier = distribution.base.currier
        actual = _bits_to_counts(distribution.base.actual_event_bits)
        page_observed[page][1] += 1
        page_expected[page][1] += 1
        currier_observed[currier][3] += 1
        currier_expected[currier][3] += 1
        currier_page_observed[currier][page][1] += 1
        currier_page_expected[currier][page][1] += 1
        for metric in range(3):
            page_observed[page][0][metric] += actual[metric]
            page_expected[page][0][metric] += distribution.expected_events[metric]
            currier_observed[currier][metric] += actual[metric]
            currier_expected[currier][metric] += distribution.expected_events[metric]
            currier_page_observed[currier][page][0][metric] += actual[metric]
            currier_page_expected[currier][page][0][metric] += distribution.expected_events[metric]

    observed_page_rows: list[tuple[float, float, float]] = []
    expected_page_rows: list[tuple[float, float, float]] = []
    page_counts: list[int] = []
    for observed, expected in zip(page_observed, page_expected):
        if observed[1] == 0 or expected[1] != observed[1]:
            raise AssertionError("reserved page has no targets or inconsistent target count")
        count = observed[1]
        page_counts.append(count)
        observed_page_rows.append(tuple(value / count for value in observed[0]))
        expected_page_rows.append(tuple(float(value / count) for value in expected[0]))

    observed_overall = tuple(
        statistics.fmean(row[metric] for row in observed_page_rows) for metric in range(3)
    )
    expected_overall = tuple(
        statistics.fmean(row[metric] for row in expected_page_rows) for metric in range(3)
    )
    observed_currier_rows = {
        currier: tuple(values[metric] / values[3] for metric in range(3))
        for currier, values in currier_observed.items()
    }
    expected_currier_rows = {
        currier: tuple(float(values[metric] / values[3]) for metric in range(3))
        for currier, values in currier_expected.items()
    }

    observed_by_currier_page: dict[str, tuple[tuple[float, float, float] | None, ...]] = {}
    expected_by_currier_page: dict[str, tuple[tuple[float, float, float] | None, ...]] = {}
    for currier in ("A", "B"):
        observed_rows: list[tuple[float, float, float] | None] = []
        expected_rows: list[tuple[float, float, float] | None] = []
        for observed, expected in zip(
            currier_page_observed[currier], currier_page_expected[currier]
        ):
            count = observed[1]
            if not count:
                observed_rows.append(None)
                expected_rows.append(None)
                continue
            observed_rows.append(tuple(value / count for value in observed[0]))
            expected_rows.append(tuple(float(value / count) for value in expected[0]))
        observed_by_currier_page[currier] = tuple(observed_rows)
        expected_by_currier_page[currier] = tuple(expected_rows)

    return AnalyticSummary(
        observed_page=tuple(observed_page_rows),
        expected_page=tuple(expected_page_rows),
        observed_overall=observed_overall,
        expected_overall=expected_overall,
        observed_currier=observed_currier_rows,
        expected_currier=expected_currier_rows,
        currier_page_observed=observed_by_currier_page,
        currier_page_expected=expected_by_currier_page,
        page_target_counts=tuple(page_counts),
        currier_target_counts={key: values[3] for key, values in currier_observed.items()},
    )


@dataclass(frozen=True)
class ReplicateSummary:
    overall: tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]
    currier: dict[
        str, tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]
    ]
    seed: int


def simulate_teacher_forced(
    distributions: tuple[TargetDistribution, ...],
    analytic: AnalyticSummary,
    *,
    order: int,
    replicates: int,
    master_seed: int = 4004,
    progress: Callable[[str], None] | None = None,
) -> ReplicateSummary:
    """Draw deterministic independent target outcomes from exact integer weights."""

    if replicates < 1:
        raise ValueError("replicates must be positive")
    seed = _seed_for_order(order, master_seed)
    rng = random.Random(seed)
    overall: list[list[float]] = [[], [], []]
    currier: dict[str, list[list[float]]] = {
        "A": [[], [], []],
        "B": [[], [], []],
    }
    page_count = len(analytic.page_target_counts)
    for replicate in range(replicates):
        page_hits = [[0, 0, 0] for _ in range(page_count)]
        currier_hits = {"A": [0, 0, 0], "B": [0, 0, 0]}
        for distribution in distributions:
            draw = rng.randrange(distribution.total_weight)
            candidate_index = bisect_right(distribution.cumulative_weights, draw)
            bits = distribution.base.event_bits[candidate_index]
            page = distribution.base.page_index
            variety = distribution.base.currier
            if bits & 0b001:
                page_hits[page][0] += 1
                currier_hits[variety][0] += 1
            if bits & 0b010:
                page_hits[page][1] += 1
                currier_hits[variety][1] += 1
            if bits & 0b100:
                page_hits[page][2] += 1
                currier_hits[variety][2] += 1
        for metric in range(3):
            overall[metric].append(
                statistics.fmean(
                    page_hits[page][metric] / analytic.page_target_counts[page]
                    for page in range(page_count)
                )
            )
            for variety in ("A", "B"):
                currier[variety][metric].append(
                    currier_hits[variety][metric]
                    / analytic.currier_target_counts[variety]
                )
        if progress is not None and (
            replicate == 0 or (replicate + 1) % 500 == 0 or replicate + 1 == replicates
        ):
            progress(f"order {order}: {replicate + 1}/{replicates} replicates")
    return ReplicateSummary(
        overall=tuple(tuple(values) for values in overall),  # type: ignore[arg-type]
        currier={
            key: tuple(tuple(values) for values in metrics)  # type: ignore[arg-type]
            for key, metrics in currier.items()
        },
        seed=seed,
    )


def _sign_counts(observed: Sequence[float], expected: Sequence[float]) -> dict[str, Any]:
    residuals = [left - right for left, right in zip(observed, expected)]
    positive = sum(value > 0 for value in residuals)
    return {
        "positive": positive,
        "zero": sum(value == 0 for value in residuals),
        "negative": sum(value < 0 for value in residuals),
        "positive_fraction": round(positive / len(residuals), 6),
    }


def _metric_comparison(
    observed: float,
    expected: float,
    replicates: Sequence[float],
    observed_pages: Sequence[float],
    expected_pages: Sequence[float],
    *,
    primary: bool,
) -> dict[str, Any]:
    quantiles = {
        label: _nearest_rank(replicates, value)
        for label, value in (("q01", 0.01), ("q05", 0.05), ("q50", 0.50), ("q95", 0.95), ("q99", 0.99))
    }
    tail = (1 + sum(value >= observed for value in replicates)) / (len(replicates) + 1)
    signs = _sign_counts(observed_pages, expected_pages)
    result = {
        "observed": round(observed, 6),
        "analytic_expectation": round(expected, 6),
        "replicate_mean": round(statistics.fmean(replicates), 6),
        "observed_minus_expectation": round(observed - expected, 6),
        "conditional_tail_area": round(tail, 6),
        "replicate_quantiles": {key: round(value, 6) for key, value in quantiles.items()},
        "page_residual_signs": signs,
    }
    if primary:
        useful_bound = observed - quantiles["q05"]
        result["favorable_95_useful_effect_bound_D95"] = round(
            useful_bound, 6
        )
        result["D95_below_0_02"] = useful_bound < 0.02
        result["advancement_checks"] = {
            "delta_at_least_0_02": observed - expected >= 0.02,
            "tail_area_at_most_0_001": tail <= 0.001,
            "positive_page_fraction_above_0_60": signs["positive"] / len(observed_pages)
            > 0.60,
        }
    return result


def _currier_comparison(
    observed: float,
    expected: float,
    replicates: Sequence[float],
    observed_pages: Sequence[float],
    expected_pages: Sequence[float],
) -> dict[str, Any]:
    tail = (1 + sum(value >= observed for value in replicates)) / (len(replicates) + 1)
    signs = _sign_counts(observed_pages, expected_pages)
    return {
        "observed": round(observed, 6),
        "analytic_expectation": round(expected, 6),
        "replicate_mean": round(statistics.fmean(replicates), 6),
        "observed_minus_expectation": round(observed - expected, 6),
        "conditional_tail_area": round(tail, 6),
        "page_residual_signs": signs,
        "advancement_checks": {
            "delta_positive": observed > expected,
            "tail_area_at_most_0_00625": tail <= 0.00625,
            "positive_page_fraction_above_0_50": signs["positive"]
            / len(observed_pages)
            > 0.50,
        },
    }


def _rate_by_currier(
    distributions: Sequence[TargetDistribution],
    value: Callable[[TargetDistribution], float],
) -> dict[str, float]:
    return {
        currier: statistics.fmean(
            value(distribution)
            for distribution in distributions
            if distribution.base.currier == currier
        )
        for currier in ("A", "B")
    }


def _training_summary(
    pages: tuple[LocalOrderPage, ...], model: ProbabilityModel
) -> dict[str, Any]:
    page_sets = {"A": set(), "B": set()}
    run_counts = Counter()
    token_counts = Counter()
    for page in pages:
        cells = _cell_by_position(page)
        for run in page.runs:
            if not run:
                continue
            currier = cells[run[0]][0][1]
            if currier not in ("A", "B"):
                continue
            page_sets[currier].add(page.page_id)
            run_counts[currier] += 1
            token_counts[currier] += len(run)
    return {
        currier: {
            "pages": len(page_sets[currier]),
            "runs": run_counts[currier],
            "surface_tokens": token_counts[currier],
            "surface_types": len(model.surface_counts[currier]),
            "discovery_singleton_types_mapped_to_UNK": sum(
                count == 1 for count in model.surface_counts[currier].values()
            ),
            "mapped_vocabulary_size_including_UNK": len(model.vocabularies[currier]),
            "mapped_UNK_tokens": model.unigrams[currier][UNK],
        }
        for currier in ("A", "B")
    }


def _model_report(
    distributions: tuple[TargetDistribution, ...],
    analytic: AnalyticSummary,
    replicates: ReplicateSummary,
    *,
    order: int,
    shared_invariants_met: bool,
) -> dict[str, Any]:
    metric_reports: dict[str, Any] = {}
    currier_reports: dict[str, Any] = {"A": {}, "B": {}}
    for metric, name in enumerate(METRIC_NAMES):
        metric_reports[name] = _metric_comparison(
            analytic.observed_overall[metric],
            analytic.expected_overall[metric],
            replicates.overall[metric],
            [row[metric] for row in analytic.observed_page],
            [row[metric] for row in analytic.expected_page],
            primary=metric < 2,
        )
        for currier in ("A", "B"):
            observed_rows = [
                row[metric]
                for row in analytic.currier_page_observed[currier]  # type: ignore[union-attr]
                if row is not None
            ]
            expected_rows = [
                row[metric]
                for row in analytic.currier_page_expected[currier]  # type: ignore[union-attr]
                if row is not None
            ]
            currier_reports[currier][name] = _currier_comparison(
                analytic.observed_currier[currier][metric],
                analytic.expected_currier[currier][metric],
                replicates.currier[currier][metric],
                observed_rows,
                expected_rows,
            )

    distinct_overall = statistics.fmean(
        float(distribution.base.distinct_cell) for distribution in distributions
    )
    distinct_currier = _rate_by_currier(
        distributions, lambda distribution: float(distribution.base.distinct_cell)
    )
    support_overall = statistics.fmean(
        float(distribution.context_supported) for distribution in distributions
    )
    support_currier = _rate_by_currier(
        distributions, lambda distribution: float(distribution.context_supported)
    )
    baseline_unk_overall = statistics.fmean(
        float(distribution.base.baseline_unk_mass) for distribution in distributions
    )
    baseline_unk_currier = _rate_by_currier(
        distributions, lambda distribution: float(distribution.base.baseline_unk_mass)
    )
    reweighted_unk_overall = statistics.fmean(
        float(distribution.reweighted_unk_mass) for distribution in distributions
    )
    reweighted_unk_currier = _rate_by_currier(
        distributions, lambda distribution: float(distribution.reweighted_unk_mass)
    )

    page_lifts: list[float] = []
    for page in range(len(analytic.page_target_counts)):
        page_lifts.append(
            statistics.fmean(
                distribution.actual_log_lift
                for distribution in distributions
                if distribution.base.page_index == page
            )
        )
    page_equal_lift = statistics.fmean(page_lifts)
    positive_lift_pages = sum(value > 0 for value in page_lifts)
    currier_lifts = _rate_by_currier(
        distributions, lambda distribution: distribution.actual_log_lift
    )

    probability_checks = {
        "all_probabilities_positive": all(
            all(value > 0 for value in distribution.probabilities)
            for distribution in distributions
        ),
        "all_probabilities_exactly_normalized": all(
            sum(distribution.probabilities, Fraction()) == 1
            for distribution in distributions
        ),
        "all_log_lifts_finite": all(
            math.isfinite(distribution.actual_log_lift) for distribution in distributions
        ),
        "integer_weights_exact": all(
            all(
                Fraction(
                    cumulative
                    - (distribution.cumulative_weights[index - 1] if index else 0),
                    distribution.total_weight,
                )
                == distribution.probabilities[index]
                for index, cumulative in enumerate(distribution.cumulative_weights)
            )
            for distribution in distributions
        ),
    }
    validity_checks = {
        "shared_H004A_invariants_met": shared_invariants_met,
        "probability_invariants_met": all(probability_checks.values()),
        "distinct_cell_rate_overall_at_least_0_80": distinct_overall >= 0.80,
        "distinct_cell_rate_A_at_least_0_80": distinct_currier["A"] >= 0.80,
        "distinct_cell_rate_B_at_least_0_80": distinct_currier["B"] >= 0.80,
        f"order_{order}_context_support_overall_at_least_{'0_50' if order == 1 else '0_10'}": support_overall
        >= (0.50 if order == 1 else 0.10),
        f"order_{order}_context_support_A_at_least_{'0_50' if order == 1 else '0_10'}": support_currier["A"]
        >= (0.50 if order == 1 else 0.10),
        f"order_{order}_context_support_B_at_least_{'0_50' if order == 1 else '0_10'}": support_currier["B"]
        >= (0.50 if order == 1 else 0.10),
        "baseline_UNK_mass_overall_at_most_0_20": baseline_unk_overall <= 0.20,
        "baseline_UNK_mass_A_at_most_0_20": baseline_unk_currier["A"] <= 0.20,
        "baseline_UNK_mass_B_at_most_0_20": baseline_unk_currier["B"] <= 0.20,
        "page_equal_predictive_log_lift_positive": page_equal_lift > 0,
        "more_than_half_page_log_lifts_positive": positive_lift_pages
        / len(page_lifts)
        > 0.50,
        "target_weighted_predictive_log_lift_A_positive": currier_lifts["A"] > 0,
        "target_weighted_predictive_log_lift_B_positive": currier_lifts["B"] > 0,
    }
    return {
        "order": order,
        "deterministic_seed": replicates.seed,
        "metrics": metric_reports,
        "currier_metrics": currier_reports,
        "diagnostics": {
            "probability_checks": probability_checks,
            "maximum_probability_normalization_error": 0.0,
            "distinct_surface_type_cell_rate": {
                "overall": round(distinct_overall, 6),
                "A": round(distinct_currier["A"], 6),
                "B": round(distinct_currier["B"], 6),
            },
            "discovery_context_support_rate": {
                "overall": round(support_overall, 6),
                "A": round(support_currier["A"], 6),
                "B": round(support_currier["B"], 6),
            },
            "baseline_candidate_UNK_mass": {
                "overall": round(baseline_unk_overall, 6),
                "A": round(baseline_unk_currier["A"], 6),
                "B": round(baseline_unk_currier["B"], 6),
            },
            "reweighted_candidate_UNK_mass": {
                "overall": round(reweighted_unk_overall, 6),
                "A": round(reweighted_unk_currier["A"], 6),
                "B": round(reweighted_unk_currier["B"], 6),
            },
            "predictive_log_lift": {
                "page_equal_mean": round(page_equal_lift, 6),
                "positive_pages": positive_lift_pages,
                "zero_pages": sum(value == 0 for value in page_lifts),
                "negative_pages": sum(value < 0 for value in page_lifts),
                "positive_page_fraction": round(
                    positive_lift_pages / len(page_lifts), 6
                ),
                "target_weighted_A": round(currier_lifts["A"], 6),
                "target_weighted_B": round(currier_lifts["B"], 6),
            },
            "maximum_integer_weight_bits": max(
                distribution.total_weight.bit_length() for distribution in distributions
            ),
        },
        "validity_checks": validity_checks,
        "comparator_valid": all(validity_checks.values()),
    }


def _validate_h004a(
    document: Document,
    report: dict[str, Any],
    reserved: tuple[LocalOrderPage, ...],
    report_sha256: str,
) -> dict[str, bool]:
    source_hash = sha256(document.source).hexdigest()
    frozen_null_cells = [
        "page",
        "I",
        "L",
        "H",
        "EVA_length",
        "paragraph_initial",
        "line_position",
    ]
    checks = {
        "source_is_pinned_ZL3b": source_hash == PINNED_ZL3B_SHA256,
        "H004A_report_hash_is_pinned": report_sha256
        == PINNED_H004A_REPORT_SHA256,
        "H004A_version_is_v1": report.get("analysis_version") == "H004-v1",
        "source_hash_matches_H004A": report.get("input", {}).get("source_sha256")
        == source_hash,
        "H004A_static_gate_met": report.get("static_matched_null_gate_met") is True,
        "reserved_page_count_matches_H004A": report.get("eligibility", {}).get(
            "eligible_reserved_pages"
        )
        == len(reserved),
        "reserved_target_count_matches_H004A": report.get("eligibility", {}).get(
            "reserved_targets"
        )
        == sum(len(page.targets) for page in reserved),
        "window_matches_H004A": report.get("protocol", {}).get("window_tokens") == 10,
        "minimum_page_targets_matches_H004A": report.get("protocol", {}).get(
            "minimum_page_targets"
        )
        == 10,
        "H004A_used_9999_permutations": report.get("protocol", {}).get(
            "permutations"
        )
        == 9999,
        "H004A_used_seed_4004": report.get("protocol", {}).get("seed") == 4004,
        "H004A_split_matches_frozen_rule": report.get("protocol", {}).get("split")
        == "SHA256('H004-v1:' + page_id), first byte < 51 is reserved",
        "H004A_null_cells_match_frozen_rule": report.get("protocol", {}).get(
            "null_cells"
        )
        == frozen_null_cells,
    }
    checks["pinned_reserved_inventory_is_33_pages_2072_targets"] = (
        len(reserved) == 33 and sum(len(page.targets) for page in reserved) == 2072
    )
    return checks


def run_h004b2_contextual_comparator(
    document: Document,
    h004a_report: dict[str, Any],
    *,
    h004a_report_sha256: str,
    replicates: int = 9999,
    master_seed: int = 4004,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Run the frozen retrospective H004-B-v2 comparator without retuning."""

    if replicates != FROZEN_REPLICATES or master_seed != FROZEN_MASTER_SEED:
        raise ValueError(
            "H004-B-v2 is frozen at 9999 replicates and master seed 4004"
        )
    if document.header.alphabet != "Eva-":
        raise ValueError("H004-B-v2 requires Eva-")
    if sha256(document.source).hexdigest() != PINNED_ZL3B_SHA256:
        raise ValueError("H004-B-v2 requires the pinned ZL3b source bytes")
    all_pages = build_local_order_pages(
        document, window=10, include_pages_without_targets=True
    )
    discovery = tuple(page for page in all_pages if not is_reserved_page(page.page_id))
    reserved = tuple(
        page
        for page in all_pages
        if is_reserved_page(page.page_id) and len(page.targets) >= 10
    )
    h004a_checks = _validate_h004a(
        document, h004a_report, reserved, h004a_report_sha256
    )
    if not all(h004a_checks.values()):
        failed = [key for key, value in h004a_checks.items() if not value]
        raise ValueError(f"H004-A invariant mismatch: {failed}")

    model = train_probability_model(discovery)
    bases = build_target_bases(reserved, model)
    if len(bases) != sum(len(page.targets) for page in reserved):
        raise AssertionError("target preparation changed H004-A inventory")
    h004a_checks.update(
        {
            "all_targets_have_exactly_10_context_positions": all(
                len(base.target.context) == 10 and len(base.context) == 10
                for base in bases
            ),
            "all_target_strata_are_A_or_B_and_match_cells": all(
                base.currier in ("A", "B")
                and base.target.stratum[1] == base.currier
                for base in bases
            ),
            "all_actual_targets_are_in_their_surface_candidate_cells": all(
                base.actual in base.candidates and sum(base.q, Fraction()) == 1
                for base in bases
            ),
            "reserved_currier_target_counts_match_H004A": {
                currier: sum(base.currier == currier for base in bases)
                for currier in ("A", "B")
            }
            == h004a_report["eligibility"]["reserved_currier_targets"],
            "reserved_currier_page_counts_match_H004A": {
                currier: sum(
                    any(target.stratum[1] == currier for target in page.targets)
                    for page in reserved
                )
                for currier in ("A", "B")
            }
            == h004a_report["eligibility"]["reserved_currier_pages"],
        }
    )

    model_reports: dict[str, Any] = {}
    for order in (1, 2):
        if progress is not None:
            progress(f"order {order}: preparing exact target distributions")
        distributions = build_target_distributions(bases, model, order=order)
        maximum_weight_bits = max(
            distribution.total_weight.bit_length() for distribution in distributions
        )
        if progress is not None:
            progress(
                f"order {order}: exact weights prepared; maximum total bit length "
                f"{maximum_weight_bits}"
            )
        if maximum_weight_bits > MAX_EXACT_WEIGHT_BITS:
            raise RuntimeError(
                f"exact integer sampling is operationally infeasible: "
                f"{maximum_weight_bits} bits exceeds {MAX_EXACT_WEIGHT_BITS}; "
                "no approximate fallback is permitted"
            )
        analytic = summarize_analytic(distributions, page_count=len(reserved))
        if order == 1:
            h004a_metric_keys = (
                "copy_or_one_edit",
                "one_edit_without_exact",
                "exact_repeat_diagnostic",
            )
            for metric, key in enumerate(h004a_metric_keys):
                h004a_checks[f"observed_{key}_matches_H004A"] = round(
                    analytic.observed_overall[metric], 6
                ) == h004a_report["held_out_static_null"][key][
                    "observed_equal_page_mean"
                ]
            for currier in ("A", "B"):
                for metric, key in enumerate(h004a_metric_keys[:2]):
                    h004a_checks[
                        f"observed_{key}_{currier}_matches_H004A"
                    ] = round(analytic.observed_currier[currier][metric], 6) == h004a_report[
                        "held_out_currier_robustness"
                    ][currier]["metrics"][key]["observed"]
            if not all(h004a_checks.values()):
                failed = [key for key, value in h004a_checks.items() if not value]
                raise ValueError(f"H004-A metric invariant mismatch: {failed}")
        simulated = simulate_teacher_forced(
            distributions,
            analytic,
            order=order,
            replicates=replicates,
            master_seed=master_seed,
            progress=progress,
        )
        model_reports[f"order_{order}"] = _model_report(
            distributions,
            analytic,
            simulated,
            order=order,
            shared_invariants_met=all(h004a_checks.values()),
        )

    both_valid = all(
        model_reports[f"order_{order}"]["comparator_valid"] for order in (1, 2)
    )
    aggregate_advancement_checks = [
        value
        for order in (1, 2)
        for name in METRIC_NAMES[:2]
        for value in model_reports[f"order_{order}"]["metrics"][name][
            "advancement_checks"
        ].values()
    ]
    currier_advancement_checks = [
        value
        for order in (1, 2)
        for currier in ("A", "B")
        for name in METRIC_NAMES[:2]
        for value in model_reports[f"order_{order}"]["currier_metrics"][currier][
            name
        ]["advancement_checks"].values()
    ]
    advanced = both_valid and all(aggregate_advancement_checks) and all(
        currier_advancement_checks
    )
    useful_margin_exclusions = [
        {
            "order": order,
            "metric": name,
            "comparator_valid": model_reports[f"order_{order}"][
                "comparator_valid"
            ],
            "D95": model_reports[f"order_{order}"]["metrics"][name][
                "favorable_95_useful_effect_bound_D95"
            ],
            "below_0_02": model_reports[f"order_{order}"]["metrics"][name][
                "D95_below_0_02"
            ],
        }
        for order in (1, 2)
        for name in METRIC_NAMES[:2]
    ]
    rejected = any(
        item["comparator_valid"] and item["below_0_02"]
        for item in useful_margin_exclusions
    )
    if rejected:
        disposition = (
            "reject H004 C/U statistics as discriminating evidence beyond this "
            "teacher-forced comparator; do not reject copying as a possible cause"
        )
    elif not both_valid:
        invalid_count = sum(
            not model_reports[f"order_{order}"]["comparator_valid"]
            for order in (1, 2)
        )
        disposition = (
            "inconclusive: both contextual comparators failed validity"
            if invalid_count == 2
            else "inconclusive: one contextual comparator failed validity"
        )
    elif advanced:
        disposition = (
            "advance only that the tested teacher-forced order-1 and order-2 "
            "comparators did not reproduce the effect"
        )
    else:
        disposition = "inconclusive under the frozen advancement and rejection gates"

    return {
        "hypothesis_id": "H004-B",
        "analysis_version": VERSION,
        "retrospective_status": (
            "frozen after H004-A inspection; reused reserved partition is not independent confirmation"
        ),
        "claim_scope": (
            "teacher-forced contextual comparator only; not a free-running Markov generator, "
            "copy/edit identification, semantic reading, or translation"
        ),
        "input": {
            "source_sha256": sha256(document.source).hexdigest(),
            "alphabet": document.header.alphabet,
            "format_version": document.header.version,
            "h004a_report_sha256": h004a_report_sha256,
        },
        "protocol": {
            "context_tokens": 10,
            "replicates_per_order": replicates,
            "master_seed": master_seed,
            "orders": [1, 2],
            "vocabulary": "discovery count >=2 plus <UNK>; discovery singletons and reserved OOV map to <UNK>",
            "probabilities": "exact Fraction P0/P1/P2; target R proportional to q * P_N/P0",
            "sampling": "independent teacher-forced target draws from precomputed exact integer cumulative weights",
            "operational_exact_weight_limit_bits": MAX_EXACT_WEIGHT_BITS,
            "candidate_order": "lexical",
            "quantiles": "nearest rank; q01/q05/q50/q95/q99",
            "tail_area": "(1 + count(replicate >= observed)) / (replicates + 1); conditional Monte Carlo, not confirmatory p-value",
        },
        "H004A_invariant_checks": h004a_checks,
        "evaluation_inventory": {
            "reserved_pages": len(reserved),
            "reserved_targets": len(bases),
            "reserved_A_targets": sum(base.currier == "A" for base in bases),
            "reserved_B_targets": sum(base.currier == "B" for base in bases),
        },
        "training": _training_summary(discovery, model),
        "models": model_reports,
        "both_comparators_valid": both_valid,
        "advancement_gate_met": advanced,
        "useful_margin_exclusions": useful_margin_exclusions,
        "H004_CU_discriminating_evidence_rejected": rejected,
        "copying_as_possible_cause_rejected": False,
        "free_running_Markov_generator_tested": False,
        "disposition": disposition,
    }


def render_h004b2_markdown(report: dict[str, Any]) -> str:
    """Render the frozen H004-B-v2 outcome without broadening its claim."""

    lines = [
        "# H004-B-v2: teacher-forced contextual comparator",
        "",
        "> Retrospective conditional model check only. This is not a free-running Markov test, a copy/edit identification, or a translation.",
        "",
        f"- Source SHA-256: `{report['input']['source_sha256']}`",
        f"- H004-A report SHA-256: `{report['input']['h004a_report_sha256']}`",
        f"- Reserved pages / targets: {report['evaluation_inventory']['reserved_pages']} / {report['evaluation_inventory']['reserved_targets']}",
        f"- Replicates per order / master seed: {report['protocol']['replicates_per_order']} / {report['protocol']['master_seed']}",
        f"- Both comparators valid: `{'yes' if report['both_comparators_valid'] else 'no'}`",
        "",
        "| Order | Metric | Observed | Analytic expectation | Delta | Tail area | Positive pages | D95 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    labels = {
        "C_copy_or_one_edit": "C: exact or one edit",
        "U_one_edit_without_exact": "U: one edit, no exact",
    }
    for order in (1, 2):
        model = report["models"][f"order_{order}"]
        for name, label in labels.items():
            item = model["metrics"][name]
            lines.append(
                f"| {order} | {label} | {item['observed']:.4f} | "
                f"{item['analytic_expectation']:.4f} | "
                f"{item['observed_minus_expectation']:+.4f} | "
                f"{item['conditional_tail_area']:.4g} | "
                f"{item['page_residual_signs']['positive']} | "
                f"{item['favorable_95_useful_effect_bound_D95']:+.4f} |"
            )
    lines.extend(["", "## Comparator validity", ""])
    for order in (1, 2):
        model = report["models"][f"order_{order}"]
        diagnostics = model["diagnostics"]
        lines.extend(
            [
                f"- Order {order}: `{'valid' if model['comparator_valid'] else 'invalid'}`; "
                f"context support overall/A/B = "
                f"{diagnostics['discovery_context_support_rate']['overall']:.2%}/"
                f"{diagnostics['discovery_context_support_rate']['A']:.2%}/"
                f"{diagnostics['discovery_context_support_rate']['B']:.2%}; "
                f"baseline UNK mass overall/A/B = "
                f"{diagnostics['baseline_candidate_UNK_mass']['overall']:.2%}/"
                f"{diagnostics['baseline_candidate_UNK_mass']['A']:.2%}/"
                f"{diagnostics['baseline_candidate_UNK_mass']['B']:.2%}; "
                f"page-equal predictive log lift = "
                f"{diagnostics['predictive_log_lift']['page_equal_mean']:+.4f}.",
            ]
        )
    lines.extend(
        [
            "",
            "## Disposition",
            "",
            report["disposition"] + ".",
            "",
            "This result does not reject copying as a possible cause and does not test a free-running Markov generator.",
        ]
    )
    return "\n".join(lines) + "\n"
