#!/usr/bin/env python3
"""v_z1_confound_2.py -- adversarial CONFOUND audit of Z1, part 2: statistics.

Independent re-implementation of Delta (deliberately naive, O(n^2) per draw, no
rank shortcuts) so the audit does not inherit t_z1.py's machinery.

Attacks, in order:
  A. Recompute the headline Delta / mean sims on TEST.
  B. DYNAMIC RANGE.  Could the statistic have SEEN a gradient in these exact
     139 strings?  Delta under the best and worst orderings of the same label
     multiset (greedy + 2-opt), against the observed value.
  C. MINIMUM DETECTABLE EFFECT.  The permutation null does not depend on the
     ordering, so the 1% critical value of the null IS the detection boundary
     for any true ordering.  Express it as a fraction of the numeral-control
     median Delta -- i.e. the effect size at which this test actually has
     power, as opposed to the effect size at which the protocol measured it.
  D. DROPPED-LOCUS gap contraction.  3 TEST loci are dropped for having no
     clean [a-z]+ token; meaning_lib renumbers around them, so pairs spanning
     a drop are scored one gap too close.  Re-run with true block positions.
  E. WRAP-AROUND.  A ring is circular; the test scores gaps linearly, so the
     truly-adjacent last/first pair is filed under g>=3.  Re-run circular.
  F. LENGTH / ALPHABET-MATCHED POWER.  The 8 numeral controls are Latin-script
     with alphabets of 3-19 and no byte-pair merges.  Voynich TEST labels are
     3.73 glyph units / 5.75 chars over an alphabet of 36 units / 19 chars.
     Build ordinal systems IN THE VOYNICH ALPHABET at the Voynich length, run
     them through the identical machinery at char level AND at glyph-unit
     level (so the frozen 20 merges are applied to them too), and ask whether
     the merges or the short labels destroy detection.
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
    c = sum(1 for x in nulls if abs(x - mu) >= d - 1e-12)
    return (1.0 + c) / (len(nulls) + 1.0)


# ---------------------------------------------------------------- naive core --
# A ring is (positions, seqs): positions[i] is the TRUE slot of seqs[i] in the
# ring (so dropped loci can leave holes), and `nslots` its block length.

def ring_pairs(positions, seqs, circular=False, nslots=None):
    """-> list of (gap, similarity) using index-pairs, similarity precomputed."""
    n = len(seqs)
    S = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            S[i][j] = S[j][i] = ML.lcs_sim(seqs[i], seqs[j])
    G = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = abs(positions[i] - positions[j])
            if circular:
                d = min(d, nslots - d)
            G[i][j] = G[j][i] = d
    return S, G


def delta_of(order, S, G):
    """order: order[slot_index] = which label sits there.  Here the labels keep
    their own similarity matrix; permuting = relabelling which seq sits in
    which position, i.e. we permute the ROWS of S against the fixed G."""
    n = len(order)
    s1 = c1 = 0.0
    s3 = c3 = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            g = G[i][j]
            s = S[order[i]][order[j]]
            if g == 1:
                s1 += s; c1 += 1
            elif g >= 3:
                s3 += s; c3 += 1
    return s1, c1, s3, c3


def pooled_delta(rings, orders):
    t1 = n1 = t3 = n3 = 0.0
    for (S, G), o in zip(rings, orders):
        a, b, c, d = delta_of(o, S, G)
        t1 += a; n1 += b; t3 += c; n3 += d
    return (t1 / n1 if n1 else 0.0) - (t3 / n3 if n3 else 0.0), n1, n3


def run(rings, nperm=NPERM, seed=SEED):
    ident = [list(range(len(S))) for S, G in rings]
    obs, n1, n3 = pooled_delta(rings, ident)
    rng = random.Random(seed)
    nulls = []
    for _ in range(nperm):
        os_ = []
        for S, G in rings:
            p = list(range(len(S)))
            rng.shuffle(p)
            os_.append(p)
        nulls.append(pooled_delta(rings, os_)[0])
    return {'delta': obs, 'p': two_sided_p(obs, nulls),
            'null_mean': mean(nulls), 'null_sd': sd_pop(nulls),
            'n_pairs_g1': int(n1), 'n_pairs_g3': int(n3),
            'nulls': nulls}


def seq_of_words(words, level):
    out = []
    for w in words:
        out.extend(ML.bpe_apply(w) if level == 'units' else list(w))
    return out


# ------------------------------------------------------------- build rings ----
pages = ML.parse_pages(str(ZL3B), comma_split=True)


def voy_rings(signs, level, use_true_slots=False, circular=False):
    """Rebuild the TEST rings from the raw loci so that dropped (illegible)
    loci can be given their true slot instead of being renumbered away."""
    out = []
    for sign in signs:
        for fo in ML.ZODIAC_SIGNS[sign]:
            p = pages.get(fo)
            if p is None:
                continue
            blocks = []
            for l in p['loci']:
                if l['type'] != 'L' or l['sub'] != 'z':
                    continue
                if l['pos'] == '@' or not blocks:
                    blocks.append([])
                blocks[-1].append(l)
            for b in blocks:
                seqs, pos = [], []
                k = 0
                for slot, l in enumerate(b):
                    if not l['words']:
                        continue
                    seqs.append(seq_of_words(l['words'], level))
                    pos.append(slot if use_true_slots else k)
                    k += 1
                if len(seqs) < MIN_RING:
                    continue
                nslots = len(b) if use_true_slots else len(seqs)
                out.append(ring_pairs(pos, seqs, circular, nslots))
    return out


print('=' * 78)
print('v_z1_confound_2  --  adversarial confound audit of Z1')
print('sha256 ZL3b ', ML.sha256(str(ZL3B)))
print('sha256 lib  ', ML.sha256(str(HERE / 'meaning_lib.py')))
print('seed', SEED, 'perms', NPERM)
print('=' * 78)

# ---- A. recompute -----------------------------------------------------------
print('\n--- A. independent recompute of the headline statistic ---')
base = voy_rings(ML.TEST_SIGNS, 'units')
rA = run(base)
print('  TEST | units | comma_split=True')
print('  Delta = %+.5f   p = %.4f   null mean %+.5f sd %.5f  (g1 pairs %d, g>=3 pairs %d)'
      % (rA['delta'], rA['p'], rA['null_mean'], rA['null_sd'],
         rA['n_pairs_g1'], rA['n_pairs_g3']))
j = json.loads((HERE / 'results' / 'z1.json').read_text(encoding='utf-8'))
t = j['results']['observed']['TEST|units|comma_split=True']
print('  t_z1.py reported     Delta = %+.5f   p = %.4f   null mean %+.5f sd %.5f'
      % (t['delta'], t['delta_p'], t['delta_null_mean'], t['delta_null_sd']))
print('  agreement on Delta: |diff| = %.2e' % abs(rA['delta'] - t['delta']))

# ---- B. dynamic range -------------------------------------------------------
print('\n--- B. DYNAMIC RANGE: what Delta could these 139 strings produce? ---')


def optimise(S, G, maximise=True, seed=SEED, restarts=6):
    """Greedy nearest-neighbour + 2-opt on the g=1 chain."""
    n = len(S)
    rng = random.Random(seed)
    best, bestv = None, None
    for r in range(restarts):
        start = rng.randrange(n)
        unused = set(range(n)); unused.discard(start)
        tour = [start]
        while unused:
            last = tour[-1]
            nxt = (max(unused, key=lambda x: S[last][x]) if maximise
                   else min(unused, key=lambda x: S[last][x]))
            tour.append(nxt); unused.discard(nxt)
        improved = True
        while improved:
            improved = False
            for i in range(n - 1):
                for k in range(i + 1, n):
                    a = tour[:i] + tour[i:k + 1][::-1] + tour[k + 1:]
                    va = sum(S[a[q]][a[q + 1]] for q in range(n - 1))
                    vt = sum(S[tour[q]][tour[q + 1]] for q in range(n - 1))
                    if (va > vt + 1e-12) if maximise else (va < vt - 1e-12):
                        tour = a; improved = True
        v = sum(S[tour[q]][tour[q + 1]] for q in range(n - 1))
        if bestv is None or ((v > bestv) if maximise else (v < bestv)):
            best, bestv = tour, v
    return best


hi = [optimise(S, G, True) for S, G in base]
lo = [optimise(S, G, False) for S, G in base]
d_hi = pooled_delta(base, hi)[0]
d_lo = pooled_delta(base, lo)[0]
print('  best ordering  (greedy+2opt) Delta = %+.5f' % d_hi)
print('  worst ordering (greedy+2opt) Delta = %+.5f' % d_lo)
print('  null max over %d draws        Delta = %+.5f' % (NPERM, max(rA['nulls'])))
print('  OBSERVED                     Delta = %+.5f' % rA['delta'])
print('  -> the statistic is not floored/ceilinged: the same label multiset can')
print('     produce Delta up to %+.4f, which is %.0f%% of the numeral median.'
      % (d_hi, 100 * d_hi / j['results']['gate']['numeral_median_delta_used']))

# ---- C. minimum detectable effect ------------------------------------------
print('\n--- C. MINIMUM DETECTABLE EFFECT (the null is ordering-independent) ---')
mu = rA['null_mean']
devs = sorted(abs(x - mu) for x in rA['nulls'])
crit = devs[int(math.ceil(0.99 * len(devs))) - 1]
med = j['results']['gate']['numeral_median_delta_used']
thr = j['results']['gate']['threshold_25pct']
print('  permutation null: mean %+.5f sd %.5f' % (mu, rA['null_sd']))
print('  two-sided 1%% critical |Delta - mu| = %.5f  ->  any true ordering with'
      % crit)
print('     Delta >= %+.5f would have been detected at p < 0.01.' % (mu + crit))
print('  numeral-control median Delta = %.5f ; gate (ii) threshold = %.5f'
      % (med, thr))
print('  minimum detectable Delta as a fraction of the numeral median: %.1f%%'
      % (100 * (mu + crit) / med))
print('  power AT THE GATE THRESHOLD itself (Delta = %.5f), normal approx:' % thr)
z = (thr - mu) / rA['null_sd']
# P(reject) = P(|N(z,1)| > crit/sd)
c = crit / rA['null_sd']


def Phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


pw_thr = (1 - Phi(c - z)) + Phi(-c - z)
print('     %.2f   (the pre-registered power figure of 1.00 is measured at the'
      % pw_thr)
print('     numeral effect size %.4f, ~25x the gate threshold, not at the bar'
      % med)
print('     the gate itself sets.)')
print('  observed Delta %+.5f, 95%% interval %+.5f .. %+.5f'
      % (rA['delta'], rA['delta'] - 1.96 * rA['null_sd'],
         rA['delta'] + 1.96 * rA['null_sd']))

# ---- D. dropped-locus gap contraction --------------------------------------
print('\n--- D. dropped illegible loci: true slots instead of renumbering ---')
rD = run(voy_rings(ML.TEST_SIGNS, 'units', use_true_slots=True))
print('  true-slot gaps   Delta = %+.5f  p = %.4f  (null mean %+.5f sd %.5f)'
      % (rD['delta'], rD['p'], rD['null_mean'], rD['null_sd']))
print('  renumbered gaps  Delta = %+.5f  p = %.4f' % (rA['delta'], rA['p']))

# ---- E. circular gaps -------------------------------------------------------
print('\n--- E. wrap-around: the ring treated as circular ---')
rE = run(voy_rings(ML.TEST_SIGNS, 'units', use_true_slots=True, circular=True))
print('  circular gaps    Delta = %+.5f  p = %.4f  (null mean %+.5f sd %.5f)'
      % (rE['delta'], rE['p'], rE['null_mean'], rE['null_sd']))

# ---- F. length / alphabet-matched ordinal systems in the Voynich alphabet ----
print('\n--- F. ordinal systems built IN THE VOYNICH ALPHABET at Voynich length ---')
labels = ML.zodiac_labels(pages)
by = ML.sign_rings(labels)
test_recs = [r for r in labels
             if r['sign'] in set(ML.TEST_SIGNS) and len(by[r['sign']][r['ring']]) >= 8]
chars = Counter(c for r in test_recs for w in r['words'] for c in w)
alpha = [c for c, _ in chars.most_common()]
print('  Voynich label char alphabet (%d): %s' % (len(alpha), ''.join(alpha)))
print('  observed mean label length: %.2f chars / %.2f glyph units'
      % (mean([len(''.join(r['words']))for r in test_recs]),
         mean([len(seq_of_words(r['words'], 'units')) for r in test_recs])))

rng = random.Random(SEED)


def rand_str(k):
    return ''.join(rng.choice(alpha) for _ in range(k))


systems = OrderedDict()
# positional: tens-part + units-part, both real EVA strings
for tk, uk, nm in ((3, 3, 'VoyPositional_3+3 (6 chars)'),
                   (2, 2, 'VoyPositional_2+2 (4 chars)'),
                   (2, 3, 'VoyPositional_2+3 (5 chars)')):
    tens = [rand_str(tk) for _ in range(4)]
    unit = [rand_str(uk) for _ in range(10)]
    systems[nm] = [tens[n // 10] + unit[n % 10] for n in range(1, 31)]
# suffix system: fixed stem + ordinal suffix that grows (like -teen / -ty)
stem = [rand_str(3) for _ in range(4)]
suf = [rand_str(2) for _ in range(10)]
systems['VoySuffix_stem+suffix'] = [suf[n % 10] + stem[n // 10] for n in range(1, 31)]
# tally / Roman-like in EVA: repeated unit glyph + repeated ten glyph
g1, g5, g10 = alpha[0], alpha[1], alpha[2]
systems['VoyTally_roman-like'] = [g10 * (n // 10) + (g5 if (n % 10) >= 5 else '')
                                  + g1 * ((n % 10) % 5) for n in range(1, 31)]
# negative: 30 real Voynich label strings in arbitrary order
real30 = [(''.join(r['words'])) for r in test_recs]
systems['NEG_real_Voynich_labels'] = random.Random(SEED).sample(real30, 30)

sizes = j['test_ring_sizes_used_for_controls']


def cut_cyclic(series, szs):
    out, k = [], 0
    for sz in szs:
        out.append([series[(k + i) % len(series)] for i in range(sz)])
        k = (k + sz) % len(series)
    return out


print('  ring sizes %s (identical to the test), %d perms, seed %d'
      % (sizes, NPERM, SEED))
print('  %-30s %-9s %-24s %-24s' % ('system', 'mean len', 'CHAR level', 'GLYPH-UNIT level'))
for nm, series in systems.items():
    line = '  %-30s %6.2f  ' % (nm, mean([len(s) for s in series]))
    for level in ('chars', 'units'):
        rings = []
        for ring in cut_cyclic(series, sizes):
            seqs = [seq_of_words([w], level) for w in ring]
            rings.append(ring_pairs(list(range(len(seqs))), seqs))
        r = run(rings)
        line += ' D=%+.4f p=%.4f%s' % (
            r['delta'], r['p'], ' *' if (r['p'] < 0.01 and r['delta'] > 0) else '  ')
    print(line)
print('  * = detected at p<0.01 in the ordinal direction.')
print('  (These are what a numeral system would look like if it were written in')
print('   the manuscript\'s own alphabet at the manuscript\'s own label length,')
print('   with the frozen 20 merges applied in the glyph-unit column.)')
