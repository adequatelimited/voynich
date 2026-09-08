#!/usr/bin/env python3
"""Adversarial verification of t_z2z3.py -- lens: NULL CORRECTNESS.
Independent reimplementation.  Does NOT import Design from t_z2z3.
"""
import json, math, random, statistics, sys
from collections import defaultdict, Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meaning_lib as M

ZL3B = r"R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt"
NPERM = 10000
SEED = 408

pages = M.parse_pages(ZL3B)
labels = M.zodiac_labels(pages)
print('labels', len(labels))


def slot_of(rec, conv):
    if conv == 'A':
        return rec['idx_in_sign']
    if conv == 'B':
        return (rec['ring'], rec['idx_in_ring'])
    cm = rec['clock_min']
    if cm is None:
        return None
    return int(math.floor(cm / 30.0 + 0.5)) % 24


def seq(rec, rep):
    if rep == 'unit':
        o = []
        for w in rec['words']:
            o.extend(M.bpe_apply(w))
        return o
    return list(''.join(rec['words']))


def build(signs, conv, rep):
    """returns groups(list of lists of global idx), slots, seqs, blocks
    blocks = finer exchangeability block id (sign, ring) for the strict null"""
    slots, seqs, groups, blocks = [], [], [], []
    p = 0
    for sg in signs:
        recs = [r for r in labels if r['sign'] == sg]
        grp = []
        for r in recs:
            s = slot_of(r, conv)
            if s is None:
                continue
            slots.append(s)
            seqs.append(seq(r, rep))
            blocks.append((sg, r['ring']))
            grp.append(p)
            p += 1
        if grp:
            groups.append(grp)
    return groups, slots, seqs, blocks


def simmat(seqs):
    n = len(seqs)
    S = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            v = M.lcs_sim(seqs[i], seqs[j])
            S[i][j] = v
            S[j][i] = v
    return S


def pairs(groups, slots):
    same, allc = [], []
    for gi in range(len(groups)):
        for gj in range(gi + 1, len(groups)):
            for a in groups[gi]:
                for b in groups[gj]:
                    allc.append((a, b))
                    if slots[a] == slots[b]:
                        same.append((a, b))
    return same, allc


def effect(assign, S, same, tot_sum, n_same, n_all):
    s = 0.0
    for a, b in same:
        s += S[assign[a]][assign[b]]
    return s / n_same - (tot_sum - s) / (n_all - n_same)


def run(groups, slots, seqs, blocks, permblocks, nperm=NPERM, seed=SEED):
    """permblocks: 'sign' (as in the test) or 'ring' (stricter, ring-preserving)"""
    S = simmat(seqs)
    same, allc = pairs(groups, slots)
    n_same, n_all = len(same), len(allc)
    tot_sum = sum(S[a][b] for a, b in allc)
    ident = list(range(len(seqs)))
    obs = effect(ident, S, same, tot_sum, n_same, n_all)
    if permblocks == 'sign':
        blk = groups
    else:
        d = defaultdict(list)
        for i, b in enumerate(blocks):
            d[b].append(i)
        blk = list(d.values())
    rng = random.Random(seed)
    nulls = []
    a = list(range(len(seqs)))
    for _ in range(nperm):
        a = list(range(len(seqs)))          # fresh identity each draw (independent of test's chain)
        for g in blk:
            v = [a[p] for p in g]
            rng.shuffle(v)
            for p, x in zip(g, v):
                a[p] = x
        nulls.append(effect(a, S, same, tot_sum, n_same, n_all))
    mu = statistics.fmean(nulls)
    sd = statistics.pstdev(nulls)
    ge2_uncentered = sum(1 for e in nulls if abs(e) >= abs(obs) - 1e-15)
    ge2_centered = sum(1 for e in nulls if abs(e - mu) >= abs(obs - mu) - 1e-15)
    ge1 = sum(1 for e in nulls if e >= obs - 1e-15)
    return {'n': len(seqs), 'n_same': n_same, 'n_all': n_all, 'effect': obs,
            'null_mean': mu, 'null_sd': sd, 'z': (obs - mu) / sd,
            'p2_uncentered': (1 + ge2_uncentered) / (nperm + 1.0),
            'p2_centered': (1 + ge2_centered) / (nperm + 1.0),
            'p1': (1 + ge1) / (nperm + 1.0)}


print('\n=== 1. Independent recompute of Z2 TEST cells, sign-level null (as tested) ===')
res = {}
for conv in 'ABC':
    for rep in ('unit', 'char'):
        g, sl, sq, bl = build(M.TEST_SIGNS, conv, rep)
        r = run(g, sl, sq, bl, 'sign')
        res[(conv, rep, 'sign')] = r
        print('conv %s %-4s  n=%d same=%d  eff=%+.6f  mu=%+.6f sd=%.6f  z=%+.2f  '
              'p2unc=%.4f  p2cent=%.4f' %
              (conv, rep, r['n'], r['n_same'], r['effect'], r['null_mean'],
               r['null_sd'], r['z'], r['p2_uncentered'], r['p2_centered']))

print('\n=== 2. STRICTER null: permute within (sign, ring) -- preserves ring membership ===')
for conv in 'ABC':
    for rep in ('unit', 'char'):
        g, sl, sq, bl = build(M.TEST_SIGNS, conv, rep)
        r = run(g, sl, sq, bl, 'ring')
        res[(conv, rep, 'ring')] = r
        print('conv %s %-4s  eff=%+.6f  mu=%+.6f sd=%.6f  z=%+.2f  p2unc=%.4f  p2cent=%.4f'
              % (conv, rep, r['effect'], r['null_mean'], r['null_sd'], r['z'],
                 r['p2_uncentered'], r['p2_centered']))

print('\n=== 3. distinct slot counts (control wraparound check, series length 30) ===')
for conv in 'ABC':
    g, sl, sq, bl = build(M.TEST_SIGNS, conv, 'unit')
    print('conv %s: %d distinct slot values across TEST signs' % (conv, len(set(sl))))

print('\n=== 4. TTR resample: with-replacement (as tested) vs without-replacement ===')
zpages = [f for fs in M.ZODIAC_SIGNS.values() for f in fs]
lab_by_page = defaultdict(list)
for x in labels:
    lab_by_page[x['page']].extend(x['words'])
txt_by_page = defaultdict(list)
for fo in zpages:
    p = pages.get(fo)
    if not p:
        continue
    for l in p['loci']:
        if l['type'] in ('P', 'C', 'R'):
            txt_by_page[fo].extend(l['words'])

by_len = {}
for pg, ws in txt_by_page.items():
    d = defaultdict(list)
    for w in ws:
        d[len(M.bpe_apply(w))].append(w)
    by_len[pg] = d

# cells: (page, matched-length) -> pool ; count how many label targets per cell
cell_targets = Counter()
cell_pool = {}
fallbacks = 0
for pg, ws in lab_by_page.items():
    for w in ws:
        L = len(M.bpe_apply(w))
        d = by_len.get(pg, {})
        if L in d and d[L]:
            key = (pg, L)
            cell_pool[key] = d[L]
        elif d:
            best = min(d.keys(), key=lambda k: (abs(k - L), k))
            key = (pg, best)
            cell_pool[key] = d[best]
            fallbacks += 1
        else:
            fallbacks += 1
            continue
        cell_targets[key] += 1

obs_words = [w for ws in lab_by_page.values() for w in ws]
obs_ttr = len(set(obs_words)) / len(obs_words)
ntok = sum(cell_targets.values())
print('label tokens %d  matched targets %d  fallbacks %d  obs TTR %.4f'
      % (len(obs_words), ntok, fallbacks, obs_ttr))
print('cells: %d ; targets>pool in %d cells'
      % (len(cell_targets),
         sum(1 for k, t in cell_targets.items() if t > len(cell_pool[k]))))
print('  cell detail (targets/pool_tokens/pool_types):')
for k in sorted(cell_targets, key=lambda k: -cell_targets[k])[:12]:
    print('   %-8s L=%d  t=%3d pool=%3d types=%3d'
          % (k[0], k[1], cell_targets[k], len(cell_pool[k]), len(set(cell_pool[k]))))

def resample_ttr(mode, ndraw=1000, seed=SEED):
    rng = random.Random(seed)
    out = []
    for _ in range(ndraw):
        samp = []
        for k, t in cell_targets.items():
            pool = cell_pool[k]
            if mode == 'repl' or t > len(pool):
                samp.extend(pool[rng.randrange(len(pool))] for _ in range(t))
            else:
                samp.extend(rng.sample(pool, t))
        out.append(len(set(samp)) / len(samp))
    return out

for mode, name in (('repl', 'WITH replacement (as tested)'),
                   ('norepl', 'WITHOUT replacement within cell')):
    t = resample_ttr(mode)
    mu, sd = statistics.fmean(t), statistics.pstdev(t)
    ge = sum(1 for x in t if x >= obs_ttr)
    print('  %-32s mean %.4f sd %.4f  max %.4f  z=%+.2f  p1(ge)=%.4f'
          % (name, mu, sd, max(t), (obs_ttr - mu) / sd, (1 + ge) / 1001.0))

# hard ceiling: TTR of the whole matched text pool itself (all types available)
allpool = [w for k in cell_targets for w in cell_pool[k]]
print('  ceiling: union of used text pools has %d tokens, %d types, TTR %.4f'
      % (len(allpool), len(set(allpool)), len(set(allpool)) / len(allpool)))

print('\n=== 5. numeral-control denominator sanity, conv C unit ===')
g, sl, sq, bl = build(M.TEST_SIGNS, 'C', 'unit')
allslots = sorted(set(sl))
rank = {s: i for i, s in enumerate(allslots)}
nums = M.numeral_controls()
effs = []
for nm, series in nums.items():
    csq = []
    for s in sl:
        w = series[rank[s] % len(series)]
        csq.append(M.bpe_apply(w))
    S = simmat(csq)
    same, allc = pairs(g, sl)
    tot = sum(S[a][b] for a, b in allc)
    ss = sum(S[a][b] for a, b in same)
    e = ss / len(same) - (tot - ss) / (len(allc) - len(same))
    effs.append(e)
    print('  %-20s effect %+.5f' % (nm, e))
print('  median clean control effect %.5f  (test JSON: 0.690697)'
      % statistics.median(effs))
print('  25%% bar = %.5f ; observed conv C unit TEST effect = %+.5f'
      % (0.25 * statistics.median(effs), res[('C', 'unit', 'sign')]['effect']))
