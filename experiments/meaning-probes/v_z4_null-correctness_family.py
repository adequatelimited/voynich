#!/usr/bin/env python3
"""v_z4_null-correctness_family.py — part 2 of the Z4 verification.

(a) Is the "two-sided" p ever different from the one-sided upper tail?
(b) Is the MI bias correctly absorbed by the null mean (Miller-Madow check)?
(c) Jackknife the passing statistic on a scale that is comparable across n
    (z = (obs - null_mean)/null_sd), not on p, which confounds effect and n.
(d) Audit the "median_debiased" figure the power claim rests on.
(e) Re-derive one non-passing p independently.
"""
import io
import json
import math
import os
import random
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import meaning_lib as ML
exec(open(os.path.join(HERE, 'v_z4_null-correctness_recompute.py'))
     .read().split("ALPHA6 = ")[0].split("OUT = []")[0]
     .replace("import meaning_lib as ML", "pass"), globals()) if False else None

REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
ZL3B = os.path.join(REPO, 'data', 'corpora', 'ZL3b-n.txt')
ALPHA6 = 0.01 / 6.0
OUT = []


def say(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


def mi_bits(pairs):
    n = len(pairs)
    j = Counter(pairs)
    rp = Counter(p for p, f in pairs)
    rf = Counter(f for p, f in pairs)
    t = 0.0
    for (p, f), c in j.items():
        t += (c / n) * math.log2((c / n) / ((rp[p] / n) * (rf[f] / n)))
    return t


def chi2_from_pairs(pairs, posvals, formvals):
    n = len(pairs)
    j = Counter(pairs)
    rp = Counter(p for p, f in pairs)
    rf = Counter(f for p, f in pairs)
    t = 0.0
    for p in posvals:
        for f in formvals:
            e = rp[p] * rf[f] / n
            if e <= 0:
                continue
            d = j.get((p, f), 0) - e
            t += d * d / e
    return t


def build(labels, level='unit'):
    ringsz = Counter((r['sign'], r['ring']) for r in labels)
    it = []
    for r in labels:
        seq = []
        for w in r['words']:
            seq.extend(ML.bpe_apply(w) if level == 'unit' else list(w))
        if not seq:
            continue
        it.append({'sign': r['sign'], 'ring': r['ring'],
                   'rank1': r['idx_in_sign'] + 1, 'iring': r['idx_in_ring'],
                   'sz': ringsz[(r['sign'], r['ring'])],
                   'p1': min(2, r['idx_in_sign'] // 10),
                   'p2': min(2, (r['idx_in_ring'] * 3) //
                             ringsz[(r['sign'], r['ring'])]),
                   'f1': seq[0], 'f2': seq[-1], 'text': r['text']})
    return it


def flatten(items, posdef):
    if posdef == 'P1':
        keyf, ordf, posf = (lambda x: x['sign'], lambda x: x['rank1'],
                            lambda x: x['p1'])
    else:
        keyf, ordf, posf = (lambda x: (x['sign'], x['ring']),
                            lambda x: x['iring'], lambda x: x['p2'])
    g = OrderedDict()
    for i, x in enumerate(items):
        g.setdefault(keyf(x), []).append(i)
    for k in g:
        g[k].sort(key=lambda i: ordf(items[i]))
    pos, f1, f2, segs = [], [], [], []
    for k, mem in g.items():
        s = len(pos)
        for i in mem:
            pos.append(posf(items[i]))
            f1.append(items[i]['f1'])
            f2.append(items[i]['f2'])
        segs.append((s, len(pos)))
    return pos, f1, f2, segs


def run(pos, form, segs, seed, B, stat='MI'):
    n = len(pos)
    pv, fv = sorted(set(pos)), sorted(set(form))
    f = (lambda pr: mi_bits(pr)) if stat == 'MI' else \
        (lambda pr: chi2_from_pairs(pr, pv, fv))
    obs = f(list(zip(pos, form)))
    rng = random.Random(seed)
    perm = list(range(n))
    nulls = []
    for _ in range(B):
        for (s, e) in segs:
            for a in range(e - 1, s, -1):
                b = rng.randint(s, a)
                perm[a], perm[b] = perm[b], perm[a]
        nulls.append(f([(pos[k], form[perm[k]]) for k in range(n)]))
    m = sum(nulls) / len(nulls)
    sd = math.sqrt(sum((v - m) ** 2 for v in nulls) / (len(nulls) - 1))
    d = abs(obs - m)
    ge2 = sum(1 for v in nulls if abs(v - m) >= d - 1e-12)
    geU = sum(1 for v in nulls if v >= obs - 1e-12)
    return {'obs': obs, 'mean': m, 'sd': sd, 'z': (obs - m) / sd if sd else 0.0,
            'p2': (1.0 + ge2) / (1.0 + B), 'pU': (1.0 + geU) / (1.0 + B),
            'ge2': ge2, 'geU': geU, 'nmin': min(nulls), 'nmax': max(nulls)}


say('=' * 78)
say('V-Z4 part 2 — two-sidedness, MI bias, jackknife, power arithmetic')
say('=' * 78)

pages = ML.parse_pages(ZL3B, comma_split=True)
lab = ML.zodiac_labels(pages, comma_split=True)
tst = [r for r in lab if r['sign'] in ML.TEST_SIGNS]
items = build(tst, 'unit')
pos1, g1, g2, s1 = flatten(items, 'P1')
pos2, f1, f2, s2 = flatten(items, 'P2')

say('')
say('[a] "two-sided" (deviation from null mean) vs one-sided upper tail,')
say('    all six registered TEST statistics, B=10000, t_z4 seeds (P1=408,P2=409)')
say('    %-28s %9s %9s %9s %9s' % ('statistic', 'p_2sided', 'p_upper', 'ge_2s', 'ge_up'))
rows = [('MI_P1_F1', pos1, g1, s1, 408, 'MI'),
        ('MI_P1_F2', pos1, g2, s1, 408, 'MI'),
        ('MI_P2_F1', pos2, f1, s2, 409, 'MI'),
        ('MI_P2_F2', pos2, f2, s2, 409, 'MI'),
        ('CHI2_prefix_by_rankblock', pos1, g1, s1, 408, 'CHI2'),
        ('CHI2_suffix_by_rankblock', pos1, g2, s1, 408, 'CHI2')]
res = {}
for nm, P, F, S, sd_, st in rows:
    r = run(P, F, S, sd_, 10000, st)
    res[nm] = r
    say('    %-28s %9.5f %9.5f %9d %9d' % (nm, r['p2'], r['pU'], r['ge2'], r['geU']))
say('    -> for every statistic with a POSITIVE effect the "two-sided" p equals')
say('       the one-sided upper-tail p exactly: the extra conservatism claimed in')
say('       t_z4 ambiguity A3 costs nothing and buys nothing here.')
say('')

say('[b] MI small-sample bias: is the null mean doing the debiasing?')
for nm, P, F in (('P2 x F1 (the passer)', pos2, f1), ('P1 x F1', pos1, g1)):
    R, C, n = len(set(P)), len(set(F)), len(P)
    mm = (R - 1) * (C - 1) / (2.0 * n * math.log(2))
    k = 'MI_P2_F1' if 'P2' in nm else 'MI_P1_F1'
    say('    %-22s R=%d C=%d n=%d  Miller-Madow bias %.4f  permutation null mean %.4f'
        % (nm, R, C, n, mm, res[k]['mean']))
say('    observed MI(P2;F1) = %.4f, of which %.0f%% is bias; debiased %.4f bits'
    % (res['MI_P2_F1']['obs'],
       100 * res['MI_P2_F1']['mean'] / res['MI_P2_F1']['obs'],
       res['MI_P2_F1']['obs'] - res['MI_P2_F1']['mean']))
say('    H(ring third) = %.4f bits, so the debiased effect is %.1f%% of the'
    % (-sum((c / len(pos2)) * math.log2(c / len(pos2))
            for c in Counter(pos2).values()),
       100 * (res['MI_P2_F1']['obs'] - res['MI_P2_F1']['mean']) /
       (-sum((c / len(pos2)) * math.log2(c / len(pos2))
             for c in Counter(pos2).values()))))
say('    position entropy.  The bias is handled correctly (null mean absorbs it).')
say('')

say('[c] jackknife of the passer on the z scale (comparable across n), B=20000 seed 777')
ringkeys = []
seen = set()
for x in items:
    k = (x['sign'], x['ring'])
    if k not in seen:
        seen.add(k)
        ringkeys.append(k)
full = run(pos2, f1, s2, 777, 20000)
say('    full        n=147  MI=%.4f  debiased=%+.4f  z=%+.2f  p=%.5f'
    % (full['obs'], full['obs'] - full['mean'], full['z'], full['p2']))
jk = []
for drop in ringkeys:
    sub = [x for x in items if (x['sign'], x['ring']) != drop]
    P, A, Bf, S = flatten(sub, 'P2')
    r = run(P, A, S, 777, 20000)
    jk.append((drop, len(sub), r))
for k, n_, r in sorted(jk, key=lambda t: t[2]['z']):
    say('    -%-18s n=%3d  MI=%.4f  debiased=%+.4f  z=%+.2f  p=%.5f %s'
        % ('%s/r%d' % k, n_, r['obs'], r['obs'] - r['mean'], r['z'], r['p2'],
           'FAILS BONF' if r['p2'] >= ALPHA6 else ''))
zs = [r['z'] for _, _, r in jk]
say('    jackknife z range %.2f .. %.2f around a full-sample z of %.2f'
    % (min(zs), max(zs), full['z']))
say('')

say('[d] audit of the power benchmark ("numeral median debiased effect")')
J = json.load(io.open(os.path.join(HERE, 'results', 'z4.json'), encoding='utf-8'))
ctrl = list(ML.numeral_controls().keys())
for t in ['MI_P1_F1', 'MI_P2_F1']:
    vals = sorted(J['power_numerals']['unit']['TEST'][s][t]['debiased']
                  for s in ctrl)
    true_med = 0.5 * (vals[3] + vals[4])
    say('    %-10s per-system debiased effects: %s'
        % (t, ', '.join('%.3f' % v for v in vals)))
    say('    %-10s t_z4 reports sorted[4] = %.4f as the "median"; the true median'
        ' of 8 values is %.4f' % ('', vals[4], true_med))
say('    (sorted[len//2] with an even n is the upper middle order statistic,')
say('     not the median.  It inflates the control benchmark, i.e. it is')
say('     conservative for the negative conclusion, but it is mislabelled.)')
say('')

say('[e] independent re-derivation of one non-passing p (MI_P1_F1)')
say('    t_z4: observed 0.20189721927326795  null_mean 0.19924154463071655  p 0.9223077692230777')
r = res['MI_P1_F1']
say('    here: observed %.17f  null_mean %.17f  p %.16f'
    % (r['obs'], r['mean'], r['p2']))
say('')

say('[f] does anything else in the family come close?  min p over the six =')
say('    %.6f (MI_P2_F1).  Second smallest = %.6f (%s).'
    % (min(res[n]['p2'] for n in res),
       sorted(res[n]['p2'] for n in res)[1],
       sorted(res, key=lambda n: res[n]['p2'])[1]))

with io.open(os.path.join(HERE, 'results', 'v_z4_null-correctness_family.stdout.txt'),
             'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
