#!/usr/bin/env python3
"""v_l1_null-correctness_f.py -- does GATE L1's verdict depend on a constant
that the pre-registration never specifies?

PROTOCOL.md says: "within-page log-odds ratio label vs. text, pooled
Mantel-Haenszel style" plus "|log-odds| >= 1 with permutation p < 0.01 after
Bonferroni over K = 25". It does not specify a continuity correction. t_l1.py
chooses a marginal correction with KAPPA = 1 (adds kappa*m1/n to both label
cells, kappa*m0/n to both text cells). The magnitude leg is highly sensitive to
that choice.

Here the whole TEST family is recomputed under five estimators, sharing ONE
permutation stream (same 10,000 draws for all five, so the comparison is not
confounded by Monte-Carlo noise):

    kappa = 0.5, 1.0 (the one used), 2.0   marginal correction
    flat Haldane-Anscombe (+0.5 to all four cells of every informative stratum)
    uncorrected

and gate leg 1 (units with |log-odds| >= 1 AND Bonferroni p < 0.01, need >= 3)
is read off each.
"""
import io, json, math, os, random, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

SEED = 408
K = 25
NPERM = int(os.environ.get('NPERM', '10000'))
REPO = 'R:/Coding/LinearA/tmp/voynich_repo'
ZL = REPO + '/data/corpora/ZL3b-n.txt'
OUT = REPO + '/experiments/meaning-probes/results'
LOG = []
def say(s=''):
    print(s); LOG.append(str(s))

# name -> (kind, kappa).  kind 'marg' | 'flat' | 'none'
EST = OrderedDict([('kappa0.5', ('marg', 0.5)), ('kappa1.0', ('marg', 1.0)),
                   ('kappa2.0', ('marg', 2.0)), ('flatHA0.5', ('flat', 0.5)),
                   ('uncorrected', ('none', 0.0))])


def topk(words, pos, k=K):
    c = Counter()
    for w in words:
        u = ML.bpe_apply(w)
        if u:
            c[u[-1] if pos == 'final' else u[0]] += 1
    return [x for x, _ in c.most_common(k)]


def build(groups, units, pos):
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


def all_logors(st, label_counts):
    """Return {est_name: [logor per unit]} for one assignment of label counts."""
    acc = {name: ([0.0] * K, [0.0] * K) for name in EST}
    for (n, m1, pool), ac in zip(st, label_counts):
        tc = Counter(x for x in pool if x >= 0)
        m0 = n - m1
        for u, t in tc.items():
            if t == n:
                continue
            A = ac.get(u, 0)
            for name, (kind, kap) in EST.items():
                if kind == 'marg':
                    p1 = kap * m1 / float(n); p0 = kap * m0 / float(n)
                    N = n + 2.0 * kap
                elif kind == 'flat':
                    p1 = p0 = kap
                    N = n + 4.0 * kap
                else:
                    p1 = p0 = 0.0
                    N = float(n)
                R, S = acc[name]
                R[u] += (A + p1) * (m0 - t + A + p0) / N
                S[u] += (m1 - A + p1) * (t - A + p0) / N
    out = {}
    for name in EST:
        R, S = acc[name]
        v = []
        for u in range(K):
            if R[u] > 1e-15 and S[u] > 1e-15:
                v.append(math.log(R[u] / S[u]))
            elif R[u] <= 1e-15 and S[u] > 1e-15:
                v.append(-99.0)          # -inf, treated as |.| >= 1
            elif S[u] <= 1e-15 and R[u] > 1e-15:
                v.append(99.0)
            else:
                v.append(0.0)
        out[name] = v
    return out


def run(tag, st, units):
    obs = all_logors(st, [Counter(x for x in p[:m1] if x >= 0)
                          for (n, m1, p) in st])
    ge = {name: [0] * K for name in EST}
    rnd = random.Random(SEED)
    for _ in range(NPERM):
        lc = [Counter(x for x in rnd.sample(pool, m1) if x >= 0)
              for (n, m1, pool) in st]
        d = all_logors(st, lc)
        for name in EST:
            o, v = obs[name], d[name]
            g = ge[name]
            for u in range(K):
                if abs(v[u]) >= abs(o[u]) - 1e-12:
                    g[u] += 1
    say('')
    say('--- %s : %d strata, %d label / %d text words'
        % (tag, len(st), sum(m1 for (n, m1, p) in st),
           sum(n - m1 for (n, m1, p) in st)))
    say('    %-8s %s' % ('unit', ''.join('%18s' % n for n in EST)))
    order = sorted(range(K), key=lambda i: obs['kappa1.0'][i])
    passers = {name: [] for name in EST}
    for u in order:
        cells = []
        for name in EST:
            lo = obs[name][u]
            p = (ge[name][u] + 1.0) / (NPERM + 1.0)
            ok = abs(lo) >= 1.0 and p * K < 0.01
            if ok:
                passers[name].append(units[u])
            cells.append('%8.3f/%.4f%s' % (lo, p * K, '*' if ok else ' '))
        say('    %-8s %s' % (units[u], ''.join('%18s' % c for c in cells)))
    say('')
    for name in EST:
        say('    %-12s gate leg 1 = %d units %-40s -> %s'
            % (name, len(passers[name]), str(passers[name]),
               'PASS' if len(passers[name]) >= 3 else 'FAIL'))
    return {name: passers[name] for name in EST}


pages = ML.parse_pages(ZL, comma_split=True)
lt = ML.label_text_by_page(pages)
words_all = ML.all_words(pages)
groups = [(pid, d['labels'], d['text']) for pid, d in lt.items()
          if pages[pid]['fnum'] % 2 == 1]

say('=' * 110)
say('v_l1 F: GATE L1 leg 1 under five continuity conventions '
    '(cell = log-odds / Bonferroni p ; * = clears leg 1). %d perms, seed %d'
    % (NPERM, SEED))
say('PROTOCOL.md specifies no continuity correction. All five are defensible '
    'readings of "pooled Mantel-Haenszel style".')
say('=' * 110)
res = OrderedDict()
for pos in ('final', 'initial'):
    un = topk(words_all, pos)
    st = build(groups, un, pos)
    res[pos] = run('TEST odd, word-%s (the PRE-REGISTERED family is "final")'
                   % pos, st, un)

say('')
say('=' * 110)
say('BOTTOM LINE -- pre-registered word-final family, TEST:')
for name in EST:
    say('  %-12s : %d units -> GATE LEG 1 %s   %s'
        % (name, len(res['final'][name]),
           'PASS' if len(res['final'][name]) >= 3 else 'FAIL',
           res['final'][name]))

with io.open(os.path.join(OUT, 'v_l1_null-correctness_f.stdout.txt'), 'w',
             encoding='utf-8') as fh:
    fh.write('\n'.join(LOG) + '\n')
with io.open(os.path.join(OUT, 'v_l1_null-correctness_f.json'), 'w',
             encoding='utf-8') as fh:
    fh.write(json.dumps(res, indent=1))
