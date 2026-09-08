#!/usr/bin/env python3
"""R2 re-derivation (independent implementation, different seed) + the (c)
entropy artefact + a hand chi-square check."""
import math, os, random, re, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

HERE = os.path.dirname(os.path.abspath(__file__))
ZL = os.path.abspath(os.path.join(HERE, '..', '..', 'data', 'corpora', 'ZL3b-n.txt'))
pages = ML.parse_pages(ZL, comma_split=True)
def fn(i): return int(re.match(r'f(\d+)', i).group(1))
recS = {p['id'] for p in pages.values() if p['meta'].get('I') == 'S'}
TESTS = {i for i in recS if fn(i) % 2 == 0}

pars = [d for d in ML.paragraphs(pages, page_ids=TESTS) if d['star']]
print('R2 TEST star paragraphs:', len(pars), ' pages:', len(set(d['page'] for d in pars)))
first_unit = [ML.bpe_apply(d['first_word'])[0] for d in pars]
lengths = [len(d['words']) for d in pars]
freq50 = [w for w, _ in Counter([w for d in pars for w in d['words']]).most_common(50)]
n = len(pars)
tail = [1 if d['star']['tail'] else 0 for d in pars]
dotted = [1 if d['star']['dotted'] else 0 for d in pars]
print('tail 1s:', sum(tail), ' dotted 1s:', sum(dotted))

# ---- independent recomputation of the top effect: tail vs presence of 'otal'
t = 'otal'
has = [1 if t in d['words'] else 0 for d in pars]
k = sum(tail)
def rate_diff(sel_set):
    a = sum(has[i] for i in sel_set)
    tot = sum(has)
    return abs(a/k - (tot-a)/(n-k))
obs_sel = set(i for i, v in enumerate(tail) if v == 1)
obs = rate_diff(obs_sel)
print("\nobserved |rate(tail) - rate(no-tail)| for type 'otal' = %.6f  "
      "(script value 0.6024590163934427)" % obs)
a = sum(has[i] for i in obs_sel); tot = sum(has)
print("   contingency: with-tail %d/%d = %.4f ; without-tail %d/%d = %.4f"
      % (a, k, a/k, tot-a, n-k, (tot-a)/(n-k)))
rng = random.Random(20260907)
cnt = 0
ND = 10000
idx = list(range(n))
for _ in range(ND):
    sel = set(rng.sample(idx, k))
    if rate_diff(sel) >= obs - 1e-12:
        cnt += 1
print('   independent permutation p = %.6f  (script 0.00049995)  [seed 20260907]'
      % ((1+cnt)/(ND+1)))
# analytic: the statistic is driven entirely by the 8 no-tail paragraphs
print('   NOTE: the no-tail group has n=%d. tot=%d occurrences of the type.' % (n-k, tot))

# ---- how many no-tail paragraphs, and are they one page?
pg = {}
for i, d in enumerate(pars):
    pg.setdefault(d['page'], [0, 0])
    pg[d['page']][0] += 1
    pg[d['page']][1] += tail[i]
print('\n   per-page tail counts (n_paras, n_tail):')
for p_, v in sorted(pg.items()):
    print('     %-7s %d/%d' % (p_, v[1], v[0]))

# ---- chi2 implementation check against an independent 2xC computation
def chi2_ref(group, cats):
    C = sorted(set(cats)); n_ = len(cats); k_ = sum(group)
    chi = 0.0
    for c in C:
        tot = sum(1 for x in cats if x == c)
        aa = sum(1 for g, x in zip(group, cats) if g == 1 and x == c)
        for o, nr in ((aa, k_), (tot-aa, n_-k_)):
            e = tot*nr/n_
            if e > 0: chi += (o-e)**2/e
    return chi
mask = 0
for i, v in enumerate(tail):
    if v: mask |= 1 << i
cats = sorted(set(first_unit))
cm = []
for c in cats:
    m = 0
    for i, u in enumerate(first_unit):
        if u == c: m |= 1 << i
    cm.append(m)
import importlib.util
spec = importlib.util.spec_from_file_location('tr', os.path.join(HERE, 't_r1r2.py'))
tr = importlib.util.module_from_spec(spec)
sys.modules['tr'] = tr
spec.loader.exec_module.__self__ if False else None
try:
    spec.loader.exec_module(tr)
except SystemExit:
    pass
print('\nchi2 check: script chi2_2xC = %.6f | independent recomputation = %.6f'
      % (tr.chi2_2xC(mask, cm, n, sum(tail)), chi2_ref(tail, first_unit)))

# ---- (c) entropy artefact -------------------------------------------------
print('\n' + '#'*72)
print('# (c) entropy: is "openers are more diverse than the control" real, or')
print('#     forced by drawing 12-18 controls WITH REPLACEMENT from 1-2 tokens?')
print('#'*72)
def gpre(w):
    for g in ML.GALLOWS:
        if w.startswith(g): return g
    return None
def strip(w):
    g = gpre(w); return (g, w[len(g):]) if g else (None, None)
recB = {p['id'] for p in pages.values()
        if p['meta'].get('I') == 'S' and p['meta'].get('L') == 'B' and 103 <= p['fnum'] <= 116}
vocab = Counter()
for d in ML.paragraphs(pages, page_ids=recB):
    vocab.update(d['words'])
for nm, ids in (('TEST', {i for i in recB if fn(i) % 2 == 0}),
                ('ALL', recB)):
    pars2 = ML.paragraphs(pages, page_ids=ids)
    pi, nonpi = [], []
    for d in pars2:
        if d['first_word']: pi.append(d['first_word'])
        nonpi.extend(d['words'][1:])
    cells = {}
    for w in nonpi:
        g, r = strip(w)
        if g is None: continue
        cells.setdefault((g, len(w)), []).append(w)
    tgt = [(w, gpre(w)) for w in pi if gpre(w)]
    matched = [t for t in tgt if (t[1], len(t[0])) in cells]
    keys = [(t[1], len(t[0])) for t in matched]
    obsH = ML.H(Counter(t[0] for t in matched))
    rng = random.Random(11)
    Hs = []
    for _ in range(2000):
        ws = [rng.choice(cells[kk]) for kk in keys]
        Hs.append(ML.H(Counter(ws)))
    mH = sum(Hs)/len(Hs)
    # the ceiling: the control CANNOT be more diverse than the number of
    # distinct words available in each cell
    cap = ML.H(Counter([Counter(cells[kk]).most_common(1)[0][0] for kk in keys]))
    avail = sum(1 for kk in keys if len(set(cells[kk])) < 3)
    maxH = math.log2(len(set(w for kk in set(keys) for w in cells[kk])))
    print('%-5s openers H=%.3f ; control-draw H=%.3f ; %d of %d control draws come '
          'from a cell with <3 distinct types (so repeats are forced); the control '
          'pool as a whole has only %d distinct types (max possible H=%.3f) against '
          '%d distinct opener types'
          % (nm, obsH, mH, avail, len(keys),
             len(set(w for kk in set(keys) for w in cells[kk])), maxH,
             len(set(t[0] for t in matched))))
