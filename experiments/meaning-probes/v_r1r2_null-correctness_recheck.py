#!/usr/bin/env python3
"""Adversarial re-derivation of t_r1r2.py statistics. Lens: null-correctness.
Independent code path; different RNG seeds where a check is a reproduction,
plus analytic cross-checks. Does not modify the test's script or JSON."""
import io, json, math, os, random, re, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

HERE = os.path.dirname(os.path.abspath(__file__))
ZL = os.path.abspath(os.path.join(HERE, '..', '..', 'data', 'corpora', 'ZL3b-n.txt'))
ND = 10000

def gpre(w):
    for g in ML.GALLOWS:
        if w.startswith(g):
            return g
    return None

def strip(w):
    g = gpre(w)
    return (g, w[len(g):]) if g else (None, None)

def msd(xs):
    n = len(xs); m = sum(xs)/n
    v = sum((x-m)**2 for x in xs)/(n-1) if n > 1 else 0.0
    return m, math.sqrt(v)

def p2(obs, null):
    m = sum(null)/len(null); d = abs(obs-m)
    return (1+sum(1 for x in null if abs(x-m) >= d-1e-12))/(len(null)+1)

pages = ML.parse_pages(ZL, comma_split=True)
recB = set()
for p in pages.values():
    if p['meta'].get('I') == 'S' and p['meta'].get('L') == 'B' and 103 <= p['fnum'] <= 116:
        recB.add(p['id'])
TEST = {i for i in recB if int(re.match(r'f(\d+)', i).group(1)) % 2 == 0}
FIT  = {i for i in recB if int(re.match(r'f(\d+)', i).group(1)) % 2 == 1}

def pools(ids):
    pars = ML.paragraphs(pages, page_ids=ids)
    pi = [d['first_word'] for d in pars if d['first_word']]
    nonpi, allw = [], []
    for d in pars:
        allw.extend(d['words']); nonpi.extend(d['words'][1:])
    nil = ML.non_initial_line_words(pages, page_ids=ids)
    return pars, pi, nonpi, allw, nil

vocab = Counter()
for d in ML.paragraphs(pages, page_ids=recB):
    vocab.update(d['words'])

print('#'*70)
print('# A. R1(a) TEST re-derivation (independent, seed 999 + analytic)')
print('#'*70)
pars, pi, nonpi, allw, nil = pools(TEST)
r_pi = sum(1 for w in pi if gpre(w))/len(pi)
r_nil = sum(1 for w in nil if gpre(w))/len(nil)
print('n_pi=%d rate=%.6f | n_nil=%d rate=%.6f | diff=%.6f'%(len(pi),r_pi,len(nil),r_nil,r_pi-r_nil))
pool = [1 if gpre(w) else 0 for w in pi+nil]
N, n1, tot = len(pool), len(pi), sum(pool)
rng = random.Random(999)
null = []
for _ in range(ND):
    s = sum(rng.sample(pool, n1))
    null.append(s/n1 - (tot-s)/(N-n1))
m, sd = msd(null)
print('perm null mean %.6f sd %.6f -> z=%.3f p=%.6f'%(m,sd,(r_pi-r_nil-m)/sd, p2(r_pi-r_nil, null)))
# analytic hypergeometric SD of the difference statistic
p_ = tot/N
var_s = n1*(N-n1)*p_*(1-p_)/(N-1)          # variance of hypergeometric count
sd_diff = math.sqrt(var_s)*(1/n1 + 1/(N-n1))
print('analytic hypergeometric sd of diff = %.6f  (script reported 0.044485)'%sd_diff)
print('analytic z = %.3f'%((r_pi-r_nil)/sd_diff))
# Fisher-exact-ish sanity: normal-approx p is astronomically small
print('=> (a) direction/magnitude confirmed; p is at the 1/10001 floor by construction.')

print()
print('#'*70)
print('# B/C. R1(b) cell structure and the null it induces')
print('#'*70)

def build(ids):
    pars, pi, nonpi, allw, nil = pools(ids)
    tgt = []
    for w in pi:
        g, r = strip(w)
        if g is None: continue
        tgt.append((w, g, r, 1 if r in vocab else 0))
    cells = {}
    for w in nonpi:
        g, r = strip(w)
        if g is None: continue
        cells.setdefault((g, len(w)), []).append((w, r, 1 if r in vocab else 0))
    return tgt, cells

for nm, ids in (('TEST', TEST), ('FIT', FIT), ('ALL', recB)):
    tgt, cells = build(ids)
    matchable = [t for t in tgt if (t[1], len(t[0])) in cells]
    ks = [(t[1], len(t[0])) for t in matchable]
    sizes = [len(cells[k]) for k in ks]
    homo = sum(1 for k in ks if len(set(c[2] for c in cells[k])) == 1)
    ntypes = [len(set(c[0] for c in cells[k])) for k in ks]
    one_type = sum(1 for x in ntypes if x == 1)
    print('%-5s tgt=%d matchable=%d  cell size: min=%d med=%d max=%d  '
          'cells with a single ATTESTATION value: %d/%d (%.1f%%)  '
          'cells with a single WORD TYPE: %d (%.1f%%)'
          % (nm, len(tgt), len(matchable), min(sizes), sorted(sizes)[len(sizes)//2],
             max(sizes), homo, len(ks), 100*homo/len(ks), one_type, 100*one_type/len(ks)))

print()
print('#'*70)
print('# D. EXACT stratified permutation test for (b): pool opener with its own')
print('#    matched cell and permute the opener/control label inside the cell.')
print('#    This is the conditionally-exact version of the same H0. Compare.')
print('#'*70)

def exact_strat_perm(tgt, cells, relaxed, seed=408, nd=ND):
    """strata: (gallows,len) [or relaxed pool]. Within a stratum with a openers
    and m controls, permute which a of the a+m members are 'openers'."""
    strata = {}
    def rel(g, L):
        for tol in (0,1,2):
            pool = []
            for dl in range(-tol, tol+1):
                pool.extend(cells.get((g, L+dl), []))
            if pool: return tuple(sorted(set((g,L+dl) for dl in range(-tol,tol+1) if (g,L+dl) in cells)))
        keys = tuple(sorted(k for k in cells if k[0]==g))
        return keys or None
    used = []
    for t in tgt:
        key = (t[1], len(t[0]))
        if relaxed:
            kk = rel(t[1], len(t[0]))
            if kk is None: continue
        else:
            if key not in cells: continue
            kk = (key,)
        strata.setdefault(kk, {'op': [], 'ct': []})['op'].append(t[3])
        used.append(t)
    for kk in strata:
        bag = []
        for k in kk: bag.extend(c[2] for c in cells[k])
        strata[kk]['ct'] = bag
    n_op = sum(len(s['op']) for s in strata.values())
    obs = sum(sum(s['op']) for s in strata.values())/n_op
    rng = random.Random(seed)
    null = []
    for _ in range(nd):
        tot = 0
        for s in strata.values():
            bag = s['op'] + s['ct']
            tot += sum(rng.sample(bag, len(s['op'])))
        null.append(tot/n_op)
    m, sd = msd(null)
    return {'n': n_op, 'obs': obs, 'ctrl': m, 'sd': sd,
            'z': (obs-m)/sd if sd else float('nan'), 'p': p2(obs, null),
            'n_strata': len(strata)}

for nm, ids in (('TEST', TEST), ('FIT', FIT), ('ALL', recB)):
    tgt, cells = build(ids)
    for relaxed in (False, True):
        r = exact_strat_perm(tgt, cells, relaxed)
        print('%-5s relaxed=%-5s EXACT-PERM n=%3d strata=%3d obs=%.4f ctrl=%.4f sd=%.4f z=%+.2f p=%.4f'
              % (nm, relaxed, r['n'], r['n_strata'], r['obs'], r['ctrl'], r['sd'], r['z'], r['p']))
    # reproduce the script's with-replacement bootstrap for direct comparison
    for relaxed in (False, True):
        if relaxed:
            def rc(g, L):
                for tol in (0,1,2):
                    pool = []
                    for dl in range(-tol,tol+1): pool.extend(cells.get((g,L+dl), []))
                    if pool: return pool
                pool = []
                for (gg,_l),v in cells.items():
                    if gg==g: pool.extend(v)
                return pool or None
            keys, sub = [], []
            for t in tgt:
                p_ = rc(t[1], len(t[0]))
                if p_ is not None: keys.append(p_); sub.append(t)
        else:
            sub = [t for t in tgt if (t[1],len(t[0])) in cells]
            keys = [cells[(t[1],len(t[0]))] for t in sub]
        obs = sum(t[3] for t in sub)/len(sub)
        rng = random.Random(777)
        null = [sum(rng.choice(p_)[2] for p_ in keys)/len(keys) for _ in range(ND)]
        m, sd = msd(null)
        print('%-5s relaxed=%-5s SCRIPT-BOOT n=%3d            obs=%.4f ctrl=%.4f sd=%.4f z=%+.2f p=%.4f'
              % (nm, relaxed, len(sub), obs, m, sd, (obs-m)/sd, p2(obs, null)))
    print()

print('#'*70)
print('# E. Frequency confound: is (b) measuring opener-hood, or word rarity?')
print('#'*70)
for nm, ids in (('TEST', TEST), ('FIT', FIT), ('ALL', recB)):
    tgt, cells = build(ids)
    def bucket(w):
        f = vocab[w]
        return 1 if f<=1 else (2 if f==2 else (3 if f<=5 else 4))
    fcells = {}
    for k, v in cells.items():
        for c in v:
            fcells.setdefault((k[0], k[1], bucket(c[0])), []).append(c)
    sub, keys = [], []
    for t in tgt:
        k = (t[1], len(t[0]), bucket(t[0]))
        if k in fcells:
            sub.append(t); keys.append(fcells[k])
    if not sub: continue
    obs = sum(t[3] for t in sub)/len(sub)
    rng = random.Random(31337)
    null = [sum(rng.choice(p_)[2] for p_ in keys)/len(keys) for _ in range(ND)]
    m, sd = msd(null)
    # observed mean word frequency, openers vs the whole control pool (token-wt)
    fo = sum(vocab[t[0]] for t in tgt)/len(tgt)
    allc = [c for v in cells.values() for c in v]
    fc = sum(vocab[c[0]] for c in allc)/len(allc)
    print('%-5s matched ALSO on word-frequency bucket: n=%d obs=%.4f ctrl=%.4f sd=%.4f z=%+.2f p=%.4f'
          % (nm, len(sub), obs, m, sd, (obs-m)/sd if sd else 0, p2(obs, null)))
    print('      mean section token-frequency of the word: openers %.2f vs control pool %.2f'
          % (fo, fc))

print()
print('#'*70)
print('# F. Why is the (c) control SD ~7e-5 on ALL? degeneracy of the null')
print('#'*70)
tgt, cells = build(recB)
sub = [t for t in tgt if (t[1],len(t[0])) in cells]
keys = [cells[(t[1],len(t[0]))] for t in sub]
rng = random.Random(4242)
t1 = []
top_types = Counter()
for _ in range(2000):
    ws = [rng.choice(p_)[0] for p_ in keys]
    c = Counter(ws)
    w, n = c.most_common(1)[0]
    t1.append(n/len(ws)); top_types[w] += 1
print('ALL: top1-share over 2000 draws: distinct values =', sorted(set(round(x,6) for x in t1))[:8],
      ' sd=%.2e' % msd(t1)[1])
print('     winning type in the control draws:', top_types.most_common(3))
big = Counter()
for k, v in cells.items():
    big[k] = len(v)
print('     largest cells:', big.most_common(5))
k0 = big.most_common(1)[0][0]
print('     cell %s has %d tokens, %d distinct types; commonest %s'
      % (k0, len(cells[k0]), len(set(c[0] for c in cells[k0])),
         Counter(c[0] for c in cells[k0]).most_common(3)))
n_openers_in_k0 = sum(1 for t in sub if (t[1],len(t[0]))==k0)
print('     %d of the %d matched openers fall in that one cell' % (n_openers_in_k0, len(sub)))
