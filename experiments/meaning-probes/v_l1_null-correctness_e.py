#!/usr/bin/env python3
"""v_l1_null-correctness_e.py -- does the |log-odds| >= 1 leg measure data or
the continuity constant?

Three of the units in play have a zero or near-zero label cell (c-: 1 label
token; chedy-final: 0; daiin-initial: 2). For a zero cell the pooled log-OR is
whatever the continuity correction makes it, so the gate's MAGNITUDE leg can be
set by KAPPA rather than by the corpus. Re-run the TEST word-initial and
word-final families at KAPPA in {0.5, 1.0, 2.0} and at the uncorrected
estimator, and count how many units clear |log-odds| >= 1.
"""
import io, math, os, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

REPO = 'R:/Coding/LinearA/tmp/voynich_repo'
ZL = REPO + '/data/corpora/ZL3b-n.txt'
OUT = REPO + '/experiments/meaning-probes/results'
K = 25
LOG = []
def say(s=''):
    print(s); LOG.append(str(s))


def topk(words, pos, k=K):
    c = Counter()
    for w in words:
        u = ML.bpe_apply(w)
        if u:
            c[u[-1] if pos == 'final' else u[0]] += 1
    return [x for x, _ in c.most_common(k)]


def strata(groups, units, pos):
    idx = {u: i for i, u in enumerate(units)}
    out = []
    for pid, lab, txt in groups:
        bl, bt = {}, {}
        for w in lab:
            u = ML.bpe_apply(w)
            if u:
                bl.setdefault(len(u), []).append(idx.get(u[-1] if pos == 'final' else u[0], -1))
        for w in txt:
            u = ML.bpe_apply(w)
            if u:
                bt.setdefault(len(u), []).append(idx.get(u[-1] if pos == 'final' else u[0], -1))
        for L, labs in sorted(bl.items()):
            txts = bt.get(L)
            if not txts:
                continue
            pool = labs + txts
            if 0 < len(labs) < len(pool):
                out.append((len(pool), len(labs), pool))
    return out


def logors(st, kappa):
    R = [0.0] * K
    S = [0.0] * K
    for (n, m1, pool) in st:
        tc = Counter(x for x in pool if x >= 0)
        ac = Counter(x for x in pool[:m1] if x >= 0)
        m0 = n - m1
        p1 = kappa * m1 / float(n)
        p0 = kappa * m0 / float(n)
        N = n + 2.0 * kappa
        for u, t in tc.items():
            if t == n:
                continue
            A = ac.get(u, 0)
            R[u] += (A + p1) * (m0 - t + A + p0) / N
            S[u] += (m1 - A + p1) * (t - A + p0) / N
    out = []
    for u in range(K):
        if R[u] > 1e-15 and S[u] > 1e-15:
            out.append(math.log(R[u] / S[u]))
        elif R[u] <= 1e-15 and S[u] > 1e-15:
            out.append(float('-inf'))
        elif S[u] <= 1e-15 and R[u] > 1e-15:
            out.append(float('inf'))
        else:
            out.append(0.0)
    return out


pages = ML.parse_pages(ZL, comma_split=True)
lt = ML.label_text_by_page(pages)
words_all = ML.all_words(pages)
groups = [(pid, d['labels'], d['text']) for pid, d in lt.items()
          if pages[pid]['fnum'] % 2 == 1]

say('=' * 78)
say('v_l1 E: sensitivity of the |log-odds| >= 1 leg to the continuity constant')
say('=' * 78)
for pos in ('final', 'initial'):
    un = topk(words_all, pos)
    st = strata(groups, un, pos)
    res = {kap: logors(st, kap) for kap in (0.5, 1.0, 2.0, 0.0)}
    say('')
    say('--- TEST odd, %s' % pos)
    say('    %-8s %10s %10s %10s %12s' %
        ('unit', 'k=0.5', 'k=1 (used)', 'k=2', 'uncorrected'))
    order = sorted(range(K), key=lambda i: res[1.0][i])
    for u in order:
        vals = [res[k][u] for k in (0.5, 1.0, 2.0, 0.0)]
        if max(abs(v) for v in vals if not math.isinf(v)) < 0.8 and \
           not any(math.isinf(v) for v in vals):
            continue
        say('    %-8s %10.4f %10.4f %10.4f %12s' %
            (un[u], vals[0], vals[1], vals[2],
             ('%.4f' % vals[3]) if not math.isinf(vals[3])
             else ('+inf' if vals[3] > 0 else '-inf')))
    for kap in (0.5, 1.0, 2.0, 0.0):
        n1 = sum(1 for v in res[kap] if abs(v) >= 1.0)
        say('    units with |log-odds| >= 1 at kappa=%.1f : %d' % (kap, n1))
    say('    pooled mean|log-odds| by kappa: ' + ', '.join(
        '%.1f=%.4f' % (k, sum(abs(v) for v in res[k] if not math.isinf(v)) /
                       sum(1 for v in res[k] if not math.isinf(v)))
        for k in (0.5, 1.0, 2.0, 0.0)))

with io.open(os.path.join(OUT, 'v_l1_null-correctness_e.stdout.txt'), 'w',
             encoding='utf-8') as fh:
    fh.write('\n'.join(LOG) + '\n')
