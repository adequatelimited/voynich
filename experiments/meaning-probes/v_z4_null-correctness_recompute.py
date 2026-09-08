#!/usr/bin/env python3
"""v_z4_null-correctness_recompute.py

ADVERSARIAL VERIFICATION of t_z4.py, lens = null-correctness.
Independent re-implementation of: MI, chi-square, the within-group permutation
null, and the p-value arithmetic.  Nothing is imported from t_z4.py.

Stdlib only.  Deterministic.
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

REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
ZL3B = os.path.join(REPO, 'data', 'corpora', 'ZL3b-n.txt')

OUT = []


def say(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)


# ---------------------------------------------------------------- statistics
def mi_bits(pairs):
    """MI in bits computed from a list of (pos, form) pairs, from scratch."""
    n = len(pairs)
    j = Counter(pairs)
    rp = Counter(p for p, f in pairs)
    rf = Counter(f for p, f in pairs)
    tot = 0.0
    for (p, f), c in j.items():
        tot += (c / n) * math.log2((c / n) / ((rp[p] / n) * (rf[f] / n)))
    return tot


def chi2_from_pairs(pairs, posvals, formvals):
    n = len(pairs)
    j = Counter(pairs)
    rp = Counter(p for p, f in pairs)
    rf = Counter(f for p, f in pairs)
    tot = 0.0
    for p in posvals:
        for f in formvals:
            e = rp[p] * rf[f] / n
            if e <= 0:
                continue
            d = j.get((p, f), 0) - e
            tot += d * d / e
    return tot


# ------------------------------------------------------------------- items
def rank_block(rank1):
    return min(2, (rank1 - 1) // 10)


def ring_third(idx0, sz):
    return min(2, (idx0 * 3) // sz)


def build(labels, level='unit'):
    ringsz = Counter((r['sign'], r['ring']) for r in labels)
    it = []
    for r in labels:
        seq = []
        for w in r['words']:
            seq.extend(ML.bpe_apply(w) if level == 'unit' else list(w))
        if not seq:
            continue
        it.append({
            'sign': r['sign'], 'ring': r['ring'], 'rank1': r['idx_in_sign'] + 1,
            'iring': r['idx_in_ring'], 'sz': ringsz[(r['sign'], r['ring'])],
            'p1': rank_block(r['idx_in_sign'] + 1),
            'p2': ring_third(r['idx_in_ring'], ringsz[(r['sign'], r['ring'])]),
            'f1': seq[0], 'f2': seq[-1], 'text': r['text'],
        })
    return it


def flatten(items, posdef):
    """Return (pos list, form1 list, form2 list, segment boundaries) in the
    SAME group/order convention as t_z4.run_position, so the RNG stream can be
    matched exactly when we want to reproduce a registered number."""
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


def perm_null(pos, form, segs, seed, B, stat='MI', posvals=None, formvals=None):
    """Permute the form vector inside each segment.  Returns observed and the
    list of null values.  Uses the same Fisher-Yates convention as t_z4 so the
    stream can be matched, but the statistic code is independent."""
    n = len(pos)
    obs = mi_bits(list(zip(pos, form))) if stat == 'MI' else \
        chi2_from_pairs(list(zip(pos, form)), posvals, formvals)
    rng = random.Random(seed)
    perm = list(range(n))
    nulls = []
    for _ in range(B):
        for (s, e) in segs:
            for a in range(e - 1, s, -1):
                b = rng.randint(s, a)
                perm[a], perm[b] = perm[b], perm[a]
        pr = [(pos[k], form[perm[k]]) for k in range(n)]
        nulls.append(mi_bits(pr) if stat == 'MI'
                     else chi2_from_pairs(pr, posvals, formvals))
    return obs, nulls


def p_twosided_meandev(obs, nulls):
    m = sum(nulls) / len(nulls)
    d = abs(obs - m)
    ge = sum(1 for v in nulls if abs(v - m) >= d - 1e-12)
    return (1.0 + ge) / (1.0 + len(nulls)), ge, m


def p_upper(obs, nulls):
    ge = sum(1 for v in nulls if v >= obs - 1e-12)
    return (1.0 + ge) / (1.0 + len(nulls)), ge


ALPHA6 = 0.01 / 6.0
ALPHA4 = 0.01 / 4.0

# =========================================================================
say('=' * 78)
say('V-Z4  null-correctness verification')
say('=' * 78)
say('sha256 ZL3b-n.txt   %s' % ML.sha256(ZL3B))
say('sha256 meaning_lib  %s' % ML.sha256(os.path.join(HERE, 'meaning_lib.py')))
say('sha256 t_z4.py      %s' % ML.sha256(os.path.join(HERE, 't_z4.py')))
say('')

# ---- 0. sanity: hand-check MI and chi2 on a tiny table --------------------
say('[0] implementation cross-check on a hand table')
# 2x2: [[10,0],[0,10]] -> MI = 1 bit exactly; chi2 = 20 exactly
tiny = [(0, 'a')] * 10 + [(1, 'b')] * 10
say('    MI([[10,0],[0,10]])   = %.10f   (exact 1.0)' % mi_bits(tiny))
say('    chi2([[10,0],[0,10]]) = %.10f   (exact 20.0)'
    % chi2_from_pairs(tiny, [0, 1], ['a', 'b']))
# 2x2 [[3,1],[1,3]]: chi2 = 8*(3*3-1*1)^2/(4*4*4*4)=... compute by hand below
t2 = [(0, 'a')] * 3 + [(0, 'b')] * 1 + [(1, 'a')] * 1 + [(1, 'b')] * 3
n = 8
chi_hand = n * (3 * 3 - 1 * 1) ** 2 / (4.0 * 4 * 4 * 4)
mi_hand = (3 / 8.) * math.log2((3 / 8.) / (.5 * .5)) * 2 + \
          (1 / 8.) * math.log2((1 / 8.) / (.5 * .5)) * 2
say('    chi2([[3,1],[1,3]])   = %.10f   (hand %.10f)'
    % (chi2_from_pairs(t2, [0, 1], ['a', 'b']), chi_hand))
say('    MI([[3,1],[1,3]])     = %.10f   (hand %.10f)' % (mi_bits(t2), mi_hand))
say('')

# ---- 1. rebuild the TEST stratum -----------------------------------------
pages = ML.parse_pages(ZL3B, comma_split=True)
lab = ML.zodiac_labels(pages, comma_split=True)
tst = [r for r in lab if r['sign'] in ML.TEST_SIGNS]
fit = [r for r in lab if r['sign'] in ML.FIT_SIGNS]
items = build(tst, 'unit')
say('[1] TEST stratum: %d label loci  (all %d, FIT %d)'
    % (len(items), len(lab), len(fit)))
pos2, f1, f2, segs2 = flatten(items, 'P2')
pos1, g1, g2, segs1 = flatten(items, 'P1')
say('    ring sizes (P2 segments): %s' % [e - s for s, e in segs2])
say('    ringthird marginal %s ; rankblock marginal %s'
    % (dict(Counter(pos2)), dict(Counter(pos1))))
say('    prefix types %d ; suffix types %d'
    % (len(set(f1)), len(set(f2))))
# how many labels sit in a ring where permutation cannot move them
frozen = sum(e - s for s, e in segs2 if e - s <= 1)
say('    labels in singleton rings (permutation is a no-op for them): %d' % frozen)
say('')

# ---- 2. reproduce the registered numbers exactly --------------------------
say('[2] independent recomputation of the six registered TEST statistics')
obs_MI_P2F1 = mi_bits(list(zip(pos2, f1)))
obs_MI_P2F2 = mi_bits(list(zip(pos2, f2)))
obs_MI_P1F1 = mi_bits(list(zip(pos1, g1)))
obs_MI_P1F2 = mi_bits(list(zip(pos1, g2)))
pv = sorted(set(pos1))
say('    observed MI(P1;F1) = %.14f   (t_z4: 0.20189721927326795)' % obs_MI_P1F1)
say('    observed MI(P1;F2) = %.14f   (t_z4: 0.16283943994084282)' % obs_MI_P1F2)
say('    observed MI(P2;F1) = %.14f   (t_z4: 0.29634347861285965)' % obs_MI_P2F1)
say('    observed MI(P2;F2) = %.14f   (t_z4: 0.24039834665997450)' % obs_MI_P2F2)
c_pref = chi2_from_pairs(list(zip(pos1, g1)), pv, sorted(set(g1)))
c_suff = chi2_from_pairs(list(zip(pos1, g2)), pv, sorted(set(g2)))
say('    observed chi2 prefix x rankblock = %.12f  (t_z4: 36.194039913603845)'
    % c_pref)
say('    observed chi2 suffix x rankblock = %.12f  (t_z4: 30.634699585173290)'
    % c_suff)
say('')

# ---- 3. reproduce the registered p for the single passer -------------------
say('[3] the single passer MI(ring-third; first unit), registered stream')
say('    NOTE: t_z4 runs the P2 permutation with seed = SEED+1 = 409.')
say('    PROTOCOL registers seed 408.  Both are computed here.')
for sd in (409, 408):
    o, nl = perm_null(pos2, f1, segs2, sd, 10000)
    p, ge, m = p_twosided_meandev(o, nl)
    pu, geu = p_upper(o, nl)
    sd_ = math.sqrt(sum((v - m) ** 2 for v in nl) / (len(nl) - 1))
    say('    seed %d : null_mean %.10f  null_sd %.10f' % (sd, m, sd_))
    say('              two-sided(mean-dev) p = %.7f  (count ge = %d)  -> %s'
        % (p, ge, 'PASS' if p < ALPHA6 else 'FAIL'))
    say('              one-sided upper     p = %.7f  (count ge = %d)  -> %s'
        % (pu, geu, 'PASS' if pu < ALPHA6 else 'FAIL'))
say('')

# ---- 4. the discreteness knife edge ---------------------------------------
say('[4] attainable p-values around the Bonferroni threshold at B = 10000')
say('    p = (1+ge)/10001 .  threshold alpha/6 = %.9f' % ALPHA6)
for ge in (13, 14, 15, 16, 17):
    p = (1.0 + ge) / 10001.0
    say('      ge = %2d -> p = %.7f  %s' % (ge, p, 'PASS' if p < ALPHA6 else 'FAIL'))
say('    => the verdict is decided by whether ge is 15 or 16: ONE draw in 10000.')
say('')

# ---- 5. an unbiased high-precision estimate of the true p -----------------
say('[5] high-precision p for MI(P2;F1), streams INDEPENDENT of seed 409')
say('    (t_z4\'s B=200000 rerun reuses seed 409, so its first 10000 draws are')
say('     literally the registered draws -- it is not an independent check.)')
tot_ge, tot_B = 0, 0
for sd in (10408, 20408, 30408, 40408):
    o, nl = perm_null(pos2, f1, segs2, sd, 50000)
    p, ge, m = p_twosided_meandev(o, nl)
    tot_ge += ge
    tot_B += 50000
    say('    seed %-6d B=50000  ge=%4d  p=%.7f  %s'
        % (sd, ge, p, 'PASS' if p < ALPHA6 else 'FAIL'))
p_pool = (1.0 + tot_ge) / (1.0 + tot_B)
se = math.sqrt(p_pool * (1 - p_pool) / tot_B)
say('    POOLED  B=%d  ge=%d  p_hat = %.7f  (MC SE %.7f)'
    % (tot_B, tot_ge, p_pool, se))
say('    Bonferroni/6 threshold %.7f  -> true p is %.2f MC SE from it'
    % (ALPHA6, (ALPHA6 - p_pool) / se))
say('    Bonferroni/4 threshold %.7f (the family the PROTOCOL registers)'
    % ALPHA4)
say('')

# ---- 6. is the null the right one?  leave-one-ring-out ---------------------
say('[6] where the effect lives: drop one ring at a time, rerun (B=20000, seed 777)')
ringkeys = []
seen = set()
for x in items:
    k = (x['sign'], x['ring'])
    if k not in seen:
        seen.add(k)
        ringkeys.append(k)
base_p = None
rows = []
for drop in [None] + ringkeys:
    sub = [x for x in items if (x['sign'], x['ring']) != drop]
    # ring thirds must be recomputed?  No: dropping a WHOLE ring leaves every
    # other ring's internal indexing untouched, so p2 is unchanged.
    P, A, Bf, S = flatten(sub, 'P2')
    o, nl = perm_null(P, A, S, 777, 20000)
    p, ge, m = p_twosided_meandev(o, nl)
    if drop is None:
        base_p = p
        say('    full 12 rings                 n=%3d  MI=%.4f  p=%.6f' % (len(sub), o, p))
    else:
        rows.append((drop, len(sub), o, p))
for k, n_, o, p in sorted(rows, key=lambda r: -r[3]):
    say('    drop %-22s n=%3d  MI=%.4f  p=%.6f  %s'
        % ('%s/r%d' % k, n_, o, p, 'FAIL' if p >= ALPHA6 else ''))
say('')

# ---- 7. what drives it: y and ok ------------------------------------------
say('[7] the contingency structure behind the passer')
tab = Counter(zip(pos2, f1))
forms = sorted(set(f1), key=lambda f: -sum(tab[(t, f)] for t in (0, 1, 2)))
rowtot = Counter(pos2)
say('    prefix   third0/%d  third1/%d  third2/%d   total'
    % (rowtot[0], rowtot[1], rowtot[2]))
for f in forms:
    v = [tab[(t, f)] for t in (0, 1, 2)]
    if sum(v) >= 3:
        say('    %-8s %5d %9d %9d %8d' % (f, v[0], v[1], v[2], sum(v)))
say('    (all other prefixes have total < 3)')
say('')

# ---- 8. family / multiplicity audit ---------------------------------------
say('[8] multiplicity audit')
say('    registered family in PROTOCOL: FOUR MI combinations -> alpha %.7f' % ALPHA4)
say('    family actually used by t_z4 : SIX (4 MI + 2 chi2) -> alpha %.7f' % ALPHA6)
say('    Statistics NOT counted in the family but reported and inspected:')
say('      FIT split (6), ALL split (6), raw-EVA level FIT+TEST (12),')
say('      comma_split=False TEST (6), ring>=6 TEST (6), GC2a FIT+TEST (12).')
say('    Only the 6 TEST/unit ones are gated, which matches the pre-registration.')
say('    But the P2 seed (409) is NOT the registered seed (408); the seed is a')
say('    free parameter that flips this particular verdict (see [3]).')

with io.open(os.path.join(HERE, 'results', 'v_z4_null-correctness.stdout.txt'),
             'w', encoding='utf-8') as fh:
    fh.write('\n'.join(OUT) + '\n')
