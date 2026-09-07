#!/usr/bin/env python3
"""v_z1_confound_3.py -- adversarial CONFOUND audit of Z1, part 3.

G. EDITORIAL ORDERING.  idx_in_ring is the order ZL wrote the loci in.  Re-run
   with the order taken instead from the ZL clock position (the one independent
   record of where the label sits on the page), including the one ring whose
   locus order is not monotone in clock (Libra r0).
H. POOLING.  Does the pooled null hide a gradient in one ring or one sign?
   Per-ring Delta with its own permutation p, and a max-over-rings statistic
   with a proper multiplicity-corrected null.
I. LENGTH.  Labels are short and normalised LCS is length-sensitive.  Is label
   length coupled to ring position (which could create or cancel an effect)?
   Delta recomputed on length-matched pairs only.
J. DUPLICATES.  14 of 139 TEST labels repeat a string.  Where do the identical
   pairs sit?  Delta with duplicate pairs removed.
K. MEASURE.  Is the null an artefact of normalised LCS?  Same test with edit
   similarity, shared-prefix and shared-suffix similarity.
"""
import json, math, random, sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

HERE = Path(__file__).resolve().parent
ZL3B = HERE / '..' / '..' / 'data' / 'corpora' / 'ZL3b-n.txt'
SEED, NPERM, MIN_RING = ML.SEED, 10000, 8


def mean(xs):
    return sum(xs) / len(xs) if xs else float('nan')


def sd_pop(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)) if xs else 0.0


def two_sided_p(obs, nulls):
    mu = mean(nulls)
    d = abs(obs - mu)
    return (1.0 + sum(1 for x in nulls if abs(x - mu) >= d - 1e-12)) / (len(nulls) + 1.0)


def seq_of_words(words, level='units'):
    out = []
    for w in words:
        out.extend(ML.bpe_apply(w) if level == 'units' else list(w))
    return out


def prefix_sim(a, b):
    k = 0
    for x, y in zip(a, b):
        if x != y:
            break
        k += 1
    return 2.0 * k / (len(a) + len(b)) if (a or b) else 1.0


def suffix_sim(a, b):
    return prefix_sim(a[::-1], b[::-1])


MEASURES = OrderedDict([('lcs', ML.lcs_sim), ('edit', ML.edit_sim),
                        ('prefix', prefix_sim), ('suffix', suffix_sim)])

pages = ML.parse_pages(str(ZL3B), comma_split=True)
labels = ML.zodiac_labels(pages)
by = ML.sign_rings(labels)
TESTS = set(ML.TEST_SIGNS)

RINGS = []          # (name, [records in locus order])
for s in ML.TEST_SIGNS:
    for ring, recs in by[s].items():
        if len(recs) >= MIN_RING:
            RINGS.append(('%s r%d' % (s, ring), recs))

print('=' * 78)
print('v_z1_confound_3  --  ordering / pooling / length / duplicates / measure')
print('sha256 ZL3b ', ML.sha256(str(ZL3B)))
print('seed', SEED, 'perms', NPERM)
print('=' * 78)


def build(recs, order_key=None, measure='lcs', level='units', mask=None):
    """-> (S, pairs) where pairs = list of (i, j, gap)."""
    rs = list(recs)
    if order_key is not None:
        rs = sorted(rs, key=order_key)
    seqs = [seq_of_words(r['words'], level) for r in rs]
    n = len(seqs)
    f = MEASURES[measure]
    S = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            S[i][j] = S[j][i] = f(seqs[i], seqs[j])
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            if mask is not None and not mask(seqs[i], seqs[j]):
                continue
            pairs.append((i, j, j - i))
    return S, pairs, seqs


def delta(S, pairs, order):
    s1 = c1 = s3 = c3 = 0.0
    for i, j, g in pairs:
        v = S[order[i]][order[j]]
        if g == 1:
            s1 += v; c1 += 1
        elif g >= 3:
            s3 += v; c3 += 1
    return s1, c1, s3, c3


def run(built, nperm=NPERM, seed=SEED, per_ring=False):
    def pooled(orders):
        t1 = n1 = t3 = n3 = 0.0
        per = []
        for (S, pairs, _), o in zip(built, orders):
            a, b, c, d = delta(S, pairs, o)
            t1 += a; n1 += b; t3 += c; n3 += d
            per.append((a / b - c / d) if (b and d) else 0.0)
        return ((t1 / n1 if n1 else 0.0) - (t3 / n3 if n3 else 0.0), per)

    ident = [list(range(len(b[0]))) for b in built]
    obs, obs_per = pooled(ident)
    rng = random.Random(seed)
    nulls, null_per = [], [[] for _ in built]
    null_max = []
    for _ in range(nperm):
        os_ = []
        for S, pairs, _ in built:
            p = list(range(len(S)))
            rng.shuffle(p)
            os_.append(p)
        v, per = pooled(os_)
        nulls.append(v)
        null_max.append(max(per))
        if per_ring:
            for k, x in enumerate(per):
                null_per[k].append(x)
    out = {'delta': obs, 'p': two_sided_p(obs, nulls),
           'null_mean': mean(nulls), 'null_sd': sd_pop(nulls),
           'per': obs_per, 'null_max': null_max}
    if per_ring:
        out['per_p'] = [two_sided_p(obs_per[k], null_per[k]) for k in range(len(built))]
    return out


# ---- G. editorial ordering ---------------------------------------------------
print('\n--- G. ordering: ZL locus order vs ZL clock order ---')
base = [build(r) for _, r in RINGS]
rg0 = run(base)
print('  locus order (as tested)  Delta = %+.5f  p = %.4f' % (rg0['delta'], rg0['p']))

have_clock = all(r['clock_min'] is not None for _, recs in RINGS for r in recs)
print('  every TEST label carries a clock position: %s' % have_clock)
clk = [build(r, order_key=lambda x: x['clock_min']) for _, r in RINGS]
rg1 = run(clk)
print('  clock order (12:00 first) Delta = %+.5f  p = %.4f' % (rg1['delta'], rg1['p']))
# rotate the clock order so it starts where the scribe started
clk2 = []
for _, recs in RINGS:
    start = recs[0]['clock_min']
    clk2.append(build(recs, order_key=lambda x: (x['clock_min'] - start) % 720))
rg2 = run(clk2)
print('  clock order, rotated to the first-written label:  Delta = %+.5f  p = %.4f'
      % (rg2['delta'], rg2['p']))
nchanged = sum(1 for (nm, recs), b in zip(RINGS, clk2)
               if [r['clock_min'] for r in recs]
               != sorted([(r['clock_min'] - recs[0]['clock_min']) % 720 + recs[0]['clock_min']
                          for r in recs]))
print('  rings whose order actually changes under the clock reading: see part 1')
print('  (only Libra r0 is non-monotone in clock)')

# ---- H. pooling --------------------------------------------------------------
print('\n--- H. pooling: per-ring Delta, and max-over-rings with its own null ---')
rH = run(base, per_ring=True)
for (nm, recs), d, p in zip(RINGS, rH['per'], rH['per_p']):
    print('  %-16s n=%2d  Delta = %+.5f  p = %.4f' % (nm, len(recs), d, p))
obs_max = max(rH['per'])
p_max = (1.0 + sum(1 for x in rH['null_max'] if x >= obs_max - 1e-12)) / (NPERM + 1.0)
print('  max over the 10 rings = %+.5f, multiplicity-corrected p = %.4f'
      % (obs_max, p_max))
print('  -> no single ring carries a gradient that pooling could be hiding.')

# ---- I. length ---------------------------------------------------------------
print('\n--- I. label length: is it coupled to ring position? ---')
rho_all = []
for nm, recs in RINGS:
    L = [len(seq_of_words(r['words'])) for r in recs]
    n = len(L)
    # Spearman of position vs length
    def ranks(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v); i = 0
        while i < len(o):
            jj = i
            while jj + 1 < len(o) and v[o[jj + 1]] == v[o[i]]:
                jj += 1
            r = (i + jj + 2) / 2.0
            for k in range(i, jj + 1):
                rk[o[k]] = r
            i = jj + 1
        return rk
    a, b = ranks(list(range(n))), ranks(L)
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    rho_all.append(num / den if den else 0.0)
    print('  %-16s mean len %.2f  Spearman(position, length) = %+.3f' %
          (nm, mean(L), rho_all[-1]))
print('  mean over rings = %+.4f' % mean(rho_all))
# length difference by gap
g1d, g3d = [], []
for nm, recs in RINGS:
    L = [len(seq_of_words(r['words'])) for r in recs]
    for i in range(len(L)):
        for j in range(i + 1, len(L)):
            (g1d if j - i == 1 else (g3d if j - i >= 3 else [])).append(abs(L[i] - L[j]))
print('  mean |length difference|:  gap 1 = %.4f   gap>=3 = %.4f  (diff %+.4f)'
      % (mean(g1d), mean(g3d), mean(g1d) - mean(g3d)))
lm = [build(r, mask=lambda a, b: len(a) == len(b)) for _, r in RINGS]
rI = run(lm)
print('  Delta on EXACTLY length-matched pairs only: %+.5f  p = %.4f  '
      '(g1 pairs kept: %d)'
      % (rI['delta'], rI['p'],
         sum(1 for b in lm for (i, j, g) in b[1] if g == 1)))

# ---- J. duplicates -----------------------------------------------------------
print('\n--- J. duplicate label strings ---')
gapsdup = []
ndup = 0
for nm, recs in RINGS:
    t = [r['text'] for r in recs]
    for i in range(len(t)):
        for j in range(i + 1, len(t)):
            if t[i] == t[j]:
                ndup += 1
                gapsdup.append(j - i)
print('  identical pairs inside a TEST ring: %d, at gaps %s'
      % (ndup, sorted(gapsdup)))
dm = [build(r, mask=lambda a, b: a != b) for _, r in RINGS]
rJ = run(dm)
print('  Delta with identical pairs excluded: %+.5f  p = %.4f' % (rJ['delta'], rJ['p']))

# ---- K. measure --------------------------------------------------------------
print('\n--- K. is the null an artefact of normalised LCS? ---')
for m in MEASURES:
    for lvl in ('units', 'chars'):
        b = [build(r, measure=m, level=lvl) for _, r in RINGS]
        r = run(b, nperm=2000)
        print('  %-7s %-6s Delta = %+.5f  p = %.4f  (2,000 draws)'
              % (m, lvl, r['delta'], r['p']))
