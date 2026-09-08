#!/usr/bin/env python3
"""v_l1_null-correctness_g.py -- exact re-derivation of the significance of the
key units, without any permutation and without any continuity correction.

Under t_l1.py's null, the label/text tag is reshuffled inside each (page x
length) stratum, holding the stratum's word multiset fixed. So the number of
label words carrying unit u in stratum i is exactly Hypergeometric(n_i, t_i,
m1_i), independent across strata. The total label count T = sum_i A_i therefore
has an exactly computable distribution -- convolve the per-stratum hypergeometrics
with a DP. No Monte Carlo, no estimator, no correction constant.

This gives an independent exact tail probability for each unit that can be held
against the reported permutation p, and it is free of every analyst choice in
t_l1.py except the strata themselves.
"""
import io, math, os, sys
from collections import Counter, OrderedDict
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

REPO = 'R:/Coding/LinearA/tmp/voynich_repo'
ZL = REPO + '/data/corpora/ZL3b-n.txt'
OUT = REPO + '/experiments/meaning-probes/results'
LOG = []
def say(s=''):
    print(s); LOG.append(str(s))

C = math.comb


def strata_for(groups, member):
    out = []
    for pid, lab, txt in groups:
        bl, bt = {}, {}
        for w in lab:
            u = ML.bpe_apply(w)
            if u:
                bl.setdefault(len(u), []).append(1 if member(u) else 0)
        for w in txt:
            u = ML.bpe_apply(w)
            if u:
                bt.setdefault(len(u), []).append(1 if member(u) else 0)
        for L, labs in sorted(bl.items()):
            txts = bt.get(L)
            if not txts:
                continue
            pool = labs + txts
            n, m1, t = len(pool), len(labs), sum(pool)
            if 0 < m1 < n and 0 < t < n:
                out.append((n, m1, t, sum(labs)))
    return out


def exact_tail(st):
    """Exact distribution of T = total label-side count, by DP over independent
    hypergeometrics. Returns (observed T, E[T], P(T <= obs), P(T >= obs))."""
    dist = {0: Fraction(1)}
    obs = 0
    ev = Fraction(0)
    for (n, m1, t, a) in st:
        obs += a
        ev += Fraction(m1 * t, n)
        lo, hi = max(0, m1 + t - n), min(m1, t)
        tot = C(n, m1)
        nd = {}
        for k, pk in dist.items():
            for x in range(lo, hi + 1):
                w = Fraction(C(t, x) * C(n - t, m1 - x), tot)
                if w:
                    nd[k + x] = nd.get(k + x, Fraction(0)) + pk * w
        dist = nd
    ple = sum(v for k, v in dist.items() if k <= obs)
    pge = sum(v for k, v in dist.items() if k >= obs)
    return obs, float(ev), float(ple), float(pge)


pages = ML.parse_pages(ZL, comma_split=True)
lt = ML.label_text_by_page(pages)

say('=' * 96)
say('v_l1 G: EXACT conditional tail probabilities (no permutation, no')
say('        continuity correction) for the units the gate turns on.')
say('        T = number of label-side words carrying the unit, summed over the')
say('        matched (page x length) strata; null = independent hypergeometrics.')
say('=' * 96)

for parity, tag in ((1, 'TEST odd'), (0, 'FIT even')):
    groups = [(pid, d['labels'], d['text']) for pid, d in lt.items()
              if pages[pid]['fnum'] % 2 == parity]
    say('')
    say('### %s' % tag)
    say('  %-34s %6s %8s %6s %12s %12s'
        % ('unit', 'T_obs', 'E[T]', 'total', 'P(T<=obs)', 'P(T>=obs)'))
    cases = [
        ('final n', lambda u: u[-1] == 'n'),
        ('final daiin (all)', lambda u: u[-1] == 'daiin'),
        ('final daiin (len>=2 words)',
         lambda u: u[-1] == 'daiin' and len(u) >= 2),
        ('final eey', lambda u: u[-1] == 'eey'),
        ('final in', lambda u: u[-1] == 'in'),
        ('initial qok', lambda u: u[0] == 'qok'),
        ('initial q', lambda u: u[0] == 'q'),
        ('initial q or qok (EVA q-)', lambda u: u[0] in ('q', 'qok')),
        ('initial c (benched gallows)', lambda u: u[0] == 'c'),
        ('initial daiin (all)', lambda u: u[0] == 'daiin'),
        ('initial daiin (len>=2 words)',
         lambda u: u[0] == 'daiin' and len(u) >= 2),
        ('initial ot', lambda u: u[0] == 'ot'),
    ]
    for name, mem in cases:
        st = strata_for(groups, mem)
        if not st:
            say('  %-34s  (no informative stratum)' % name)
            continue
        obs, ev, ple, pge = exact_tail(st)
        tot = sum(t for (n, m1, t, a) in st)
        say('  %-34s %6d %8.2f %6d %12.3e %12.3e'
            % (name, obs, ev, tot, ple, pge))

say('')
say('Read: a two-sided exact p is ~2*min(P(T<=obs), P(T>=obs)). Compare with')
say('the Bonferroni threshold 0.01/25 = 4.0e-4 for a one-family reading, or')
say('0.01/50 = 2.0e-4 if the added word-initial family is corrected honestly.')

with io.open(os.path.join(OUT, 'v_l1_null-correctness_g.stdout.txt'), 'w',
             encoding='utf-8') as fh:
    fh.write('\n'.join(LOG) + '\n')
