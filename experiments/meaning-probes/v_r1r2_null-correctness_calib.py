#!/usr/bin/env python3
"""Decisive check: does the (b)/(c) null in t_r1r2.py control type-I error?

Under the test's own H0 -- 'a paragraph-opener gallows word behaves like a
non-opener gallows word of the same gallows and the same length' -- the
opener/control labels are exchangeable WITHIN each (gallows,length) cell.
So: permute the labels within each cell to manufacture data where H0 is TRUE by
construction, then run the script's own statistic and null on it, and count how
often it rejects at p<0.05.  A correct null rejects ~5% of the time.
"""
import math, os, random, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

HERE = os.path.dirname(os.path.abspath(__file__))
ZL = os.path.abspath(os.path.join(HERE, '..', '..', 'data', 'corpora', 'ZL3b-n.txt'))

def gpre(w):
    for g in ML.GALLOWS:
        if w.startswith(g):
            return g
    return None

def strip(w):
    g = gpre(w)
    return (g, w[len(g):]) if g else (None, None)

pages = ML.parse_pages(ZL, comma_split=True)
recB = {p['id'] for p in pages.values()
        if p['meta'].get('I') == 'S' and p['meta'].get('L') == 'B' and 103 <= p['fnum'] <= 116}
def fn(i): return int(re.match(r'f(\d+)', i).group(1))
STRATA = {'TEST': {i for i in recB if fn(i) % 2 == 0},
          'FIT':  {i for i in recB if fn(i) % 2 == 1},
          'ALL':  recB}
vocab = Counter()
for d in ML.paragraphs(pages, page_ids=recB):
    vocab.update(d['words'])

def build(ids):
    pars = ML.paragraphs(pages, page_ids=ids)
    pi, nonpi = [], []
    for d in pars:
        if d['first_word']: pi.append(d['first_word'])
        nonpi.extend(d['words'][1:])
    tgt = []
    for w in pi:
        g, r = strip(w)
        if g is not None:
            tgt.append((w, g, r, 1 if r in vocab else 0))
    cells = {}
    for w in nonpi:
        g, r = strip(w)
        if g is None: continue
        cells.setdefault((g, len(w)), []).append((w, r, 1 if r in vocab else 0))
    return tgt, cells

# ---------------------------------------------------------------- part 1 ----
print('#'*72)
print('# 1. Per-stratum composition: how many openers vs how many controls?')
print('#'*72)
for nm in ('TEST', 'FIT', 'ALL'):
    tgt, cells = build(STRATA[nm])
    matched = [t for t in tgt if (t[1], len(t[0])) in cells]
    per = {}
    for t in matched:
        per.setdefault((t[1], len(t[0])), [0, 0])[0] += 1
    for k, v in per.items():
        v[1] = len(cells[k])
    n_op = len(matched)
    op_in_small = sum(v[0] for v in per.values() if v[1] < 5)
    op_in_tiny  = sum(v[0] for v in per.values() if v[1] <= 2)
    # opener share of the pooled bag, weighted by openers
    contam = sum(v[0] * v[0] / (v[0] + v[1]) for v in per.values()) / n_op
    print('%-5s %d matched openers in %d cells; openers whose control cell has '
          '<=2 tokens: %d (%.0f%%), <5 tokens: %d (%.0f%%); opener share of the '
          'pooled bag (opener-weighted) = %.3f'
          % (nm, n_op, len(per), op_in_tiny, 100*op_in_tiny/n_op,
             op_in_small, 100*op_in_small/n_op, contam))
    rows = sorted(per.items(), key=lambda kv: -kv[1][0])[:8]
    print('      biggest opener cells (gallows,len): ' + ', '.join(
        '%s%d:%dop/%dctrl' % (k[0], k[1], v[0], v[1]) for k, v in rows))

# ---------------------------------------------------------------- part 2 ----
print()
print('#'*72)
print('# 2. TYPE-I ERROR of the script\'s (b) null, measured under H0-true data')
print('#'*72)
print('#    (analytic z for the script\'s bootstrap null: mean = sum of cell')
print('#     means / n, var = sum p_i(1-p_i)/n^2 -- exact for its construction)')

def boot_z(op_bits, cell_bits_by_key, keys):
    """z of the script's null: obs vs the with-replacement cell-draw dist."""
    n = len(op_bits)
    obs = sum(op_bits)/n
    m = 0.0; v = 0.0
    for k in keys:
        b = cell_bits_by_key[k]
        p = sum(b)/len(b)
        m += p; v += p*(1-p)
    m /= n; v /= n*n
    sd = math.sqrt(v)
    return obs, m, sd, ((obs-m)/sd if sd > 0 else 0.0)

def simulate(nm, nsim=2000, seed=408):
    tgt, cells = build(STRATA[nm])
    matched = [t for t in tgt if (t[1], len(t[0])) in cells]
    keys = [(t[1], len(t[0])) for t in matched]
    bags = {}
    for k in set(keys):
        bags[k] = [c[2] for c in cells[k]]
    n_op_per = Counter(keys)
    rng = random.Random(seed)
    rej05 = rej01 = rej001 = 0
    zs = []
    for _ in range(nsim):
        new_cells = {}
        new_op = {}
        for k, nk in n_op_per.items():
            # H0: opener labels exchangeable with control labels inside the cell
            bag = bags[k] + [t[3] for t in matched if (t[1], len(t[0])) == k]
            rng.shuffle(bag)
            new_op[k] = bag[:nk]
            new_cells[k] = bag[nk:] or bag[:1]
        op_bits = [b for k in n_op_per for b in new_op[k]]
        kk = [k for k in n_op_per for _ in range(n_op_per[k])]
        obs, m, sd, z = boot_z(op_bits, new_cells, kk)
        zs.append(z)
        if abs(z) > 1.959964: rej05 += 1
        if abs(z) > 2.575829: rej01 += 1
        if abs(z) > 3.290527: rej001 += 1
    return rej05/nsim, rej01/nsim, rej001/nsim, zs

for nm in ('TEST', 'FIT', 'ALL'):
    r5, r1, r01, zs = simulate(nm)
    m = sum(zs)/len(zs)
    sdz = math.sqrt(sum((x-m)**2 for x in zs)/(len(zs)-1))
    print('%-5s H0-true simulations: rejection rate at nominal 0.05 = %.3f '
          '(should be 0.050) | at 0.01 = %.3f (0.010) | at 0.001 = %.4f (0.0010)'
          % (nm, r5, r1, r01))
    print('      the null-z it produces under H0 has mean %+.3f and SD %.3f '
          '(a correct null gives mean 0, SD 1.00)' % (m, sdz))

# ---------------------------------------------------------------- part 3 ----
print()
print('#'*72)
print('# 3. The (c) control-null degeneracy that produced -693 SD on ALL')
print('#'*72)
tgt, cells = build(recB)
matched = [t for t in tgt if (t[1], len(t[0])) in cells]
keys = [(t[1], len(t[0])) for t in matched]
kc = Counter(keys)
for k, n in kc.most_common(6):
    c = Counter(x[0] for x in cells[k])
    dom, dn = c.most_common(1)[0]
    print("  cell %-8s %3d openers | %3d control tokens, %2d types; commonest "
          "'%s' x%d = %.0f%% of the cell"
          % (str(k), n, len(cells[k]), len(c), dom, dn, 100*dn/len(cells[k])))
k = ('p', 9)
if k in cells:
    c = Counter(x[0] for x in cells[k])
    print("  cell ('p',9): %d openers matched to it, control pool %d tokens, "
          "commonest %s" % (kc.get(k, 0), len(cells[k]), c.most_common(3)))
print('  => the (c) "control" top-1 share is near-deterministic, so its SD is')
print('     ~1e-4 and the reported -693 SD / -358 SD are meaningless.')
