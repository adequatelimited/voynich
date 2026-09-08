#!/usr/bin/env python3
"""Adversarial check #2: the Z3 TTR-resample null.
The test draws WITH replacement from small per-(page,length) token pools.
Here: (a) reproduce, (b) without-replacement, (c) a clean exchangeability
permutation null (pool label+text tokens inside each cell, reassign tags).
"""
import random, statistics, sys
from collections import defaultdict, Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meaning_lib as M

ZL3B = r"R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt"
SEED = 408
pages = M.parse_pages(ZL3B)
labels = M.zodiac_labels(pages)

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

# ---- Z3 primary gate, independent recompute -------------------------------
strings = [x['text'] for x in labels]
print('Z3 gate: %d loci, %d distinct, ratio %.4f  (threshold <0.5 -> %s)'
      % (len(strings), len(set(strings)), len(set(strings)) / len(strings),
         'PASS' if len(set(strings)) / len(strings) < 0.5 else 'FAIL'))
lw = [w for x in labels for w in x['words']]
print('label word tokens %d types %d TTR %.4f' % (len(lw), len(set(lw)),
                                                  len(set(lw)) / len(lw)))

obs_words = [w for ws in lab_by_page.values() for w in ws]
obs_ttr = len(set(obs_words)) / len(obs_words)

cell_lab, cell_txt = defaultdict(list), {}
for pg, ws in lab_by_page.items():
    for w in ws:
        L = len(M.bpe_apply(w))
        d = by_len.get(pg, {})
        if not d:
            continue
        key = (pg, L) if (L in d and d[L]) else \
              (pg, min(d.keys(), key=lambda k: (abs(k - L), k)))
        cell_lab[key].append(w)
        cell_txt[key] = d[key[1]]

N = sum(len(v) for v in cell_lab.values())
print('\nmatched label tokens %d of %d ; %d cells' % (N, len(obs_words), len(cell_lab)))


def draw(mode, ndraw=1000, seed=SEED):
    rng = random.Random(seed)
    out = []
    for _ in range(ndraw):
        s = []
        for k, labs in cell_lab.items():
            t, pool = len(labs), cell_txt[k]
            if mode == 'repl':
                s.extend(pool[rng.randrange(len(pool))] for _ in range(t))
            elif mode == 'norepl':
                s.extend(rng.sample(pool, t) if t <= len(pool)
                         else [pool[rng.randrange(len(pool))] for _ in range(t)])
            else:                       # exchangeability: pool labels+text, retag
                both = labs + pool
                rng.shuffle(both)
                s.extend(both[:t])
        out.append(len(set(s)) / len(s))
    return out


print('\nobserved label TTR %.4f' % obs_ttr)
for mode, name in (('repl', 'WITH replacement  (as the test does)'),
                   ('norepl', 'WITHOUT replacement in cell'),
                   ('exch', 'exchangeability permutation (label/text retag)')):
    t = draw(mode)
    mu, sd = statistics.fmean(t), statistics.pstdev(t)
    ge = sum(1 for x in t if x >= obs_ttr)
    le = sum(1 for x in t if x <= obs_ttr)
    p2 = min(1.0, 2 * min(1 + ge, 1 + le) / 1001.0)
    print('  %-48s mu=%.4f sd=%.4f  z=%+6.2f  p1=%.4f  p2=%.4f'
          % (name, mu, sd, (obs_ttr - mu) / sd, (1 + ge) / 1001.0, p2))
