#!/usr/bin/env python3
"""Adversarial recon 1 for z2z3: structural confounds.

Does NOT modify t_z2z3.py or its JSON.  Read-only checks:
  1. Lz loci dropped by the clean parser (empty word list) -- do drops shift
     the idx_in_sign / idx_in_ring counters?  Are they position-correlated?
  2. Page-level metadata of the 12 zodiac folios (hand, quire, language, illus).
  3. Label length by slot; length mismatch of same-slot vs different-slot
     cross-sign pairs (a length confound could depress same-slot similarity).
  4. Clock coverage per sign and the clock of the FIRST transcribed label of
     each ring (rotation offset across signs).
  5. TTR resample pool sizes -- ceiling on the achievable resample TTR.
"""
import sys, math, re, statistics
from collections import Counter, defaultdict, OrderedDict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meaning_lib as M

ZL3B = r"R:/Coding/LinearA/tmp/voynich_repo/data/corpora/ZL3b-n.txt"

pages = M.parse_pages(ZL3B)
labels = M.zodiac_labels(pages)
print('sha256 ZL3b', M.sha256(ZL3B))
print('labels parsed:', len(labels))

# ---------------------------------------------------------------- 1. drops --
print('\n== 1. Lz loci dropped by the clean parser ==')
tot_lz = 0
drops = []
per_sign = OrderedDict()
for sign, folios in M.ZODIAC_SIGNS.items():
    kept = dropped = 0
    seq = []
    for fo in folios:
        p = pages.get(fo)
        if not p:
            continue
        for l in p['loci']:
            if l['type'] != 'L' or l['sub'] != 'z':
                continue
            tot_lz += 1
            if l['words']:
                kept += 1
                seq.append('K')
            else:
                dropped += 1
                seq.append('D')
                drops.append((sign, fo, l['n'], l['pos'], l['raw'][:60]))
    per_sign[sign] = (kept, dropped, ''.join(seq))
for s, (k, d, seq) in per_sign.items():
    print('  %-12s kept %3d dropped %d  %s' % (s, k, d, seq if d else ''))
print('  total Lz loci %d, kept %d, dropped %d' % (tot_lz, len(labels), tot_lz - len(labels)))
for d in drops:
    print('   DROP', d)

# ------------------------------------------------------------- 2. metadata --
print('\n== 2. zodiac page metadata ==')
for sign, folios in M.ZODIAC_SIGNS.items():
    for fo in folios:
        p = pages.get(fo)
        print('  %-12s %-6s %s' % (sign, fo, p['meta'] if p else 'MISSING'))

# ------------------------------------------------- 3. length / slot confound --
print('\n== 3. label length ==')
def ulen(r):
    return len(M.seq if False else [u for w in r['words'] for u in M.bpe_apply(w)])
for split, signs in (('FIT', M.FIT_SIGNS), ('TEST', M.TEST_SIGNS)):
    Ls = [ulen(r) for r in labels if r['sign'] in signs]
    print('  %s glyph-unit label length: n=%d mean %.2f sd %.2f min %d max %d'
          % (split, len(Ls), statistics.fmean(Ls), statistics.pstdev(Ls), min(Ls), max(Ls)))

def slot_of(rec, conv):
    if conv == 'A':
        return rec['idx_in_sign']
    if conv == 'B':
        return (rec['ring'], rec['idx_in_ring'])
    cm = rec['clock_min']
    return None if cm is None else int(math.floor(cm / 30.0 + 0.5)) % 24

for conv in 'ABC':
    for split, signs in (('TEST',  M.TEST_SIGNS),):
        recs = [r for r in labels if r['sign'] in signs and slot_of(r, conv) is not None]
        bysign = defaultdict(list)
        for r in recs:
            bysign[r['sign']].append(r)
        same_dl, diff_dl = [], []
        same_sim, diff_sim = [], []
        sg = list(bysign)
        for i in range(len(sg)):
            for j in range(i + 1, len(sg)):
                for a in bysign[sg[i]]:
                    for b in bysign[sg[j]]:
                        dl = abs(ulen(a) - ulen(b))
                        if slot_of(a, conv) == slot_of(b, conv):
                            same_dl.append(dl)
                        else:
                            diff_dl.append(dl)
        print('  conv %s TEST: mean |len diff| same-slot %.3f (n=%d) vs diff-slot %.3f (n=%d)'
              % (conv, statistics.fmean(same_dl), len(same_dl),
                 statistics.fmean(diff_dl), len(diff_dl)))

# --------------------------------------------------- 4. clock / rotation ----
print('\n== 4. clock coverage and ring start positions ==')
sr = M.sign_rings(labels)
for sign, rings in sr.items():
    for ring, rs in rings.items():
        clocks = [r['clock'] for r in rs]
        n_clock = sum(1 for c in clocks if c)
        print('  %-12s ring %d  n=%2d  clocks %2d  first=%s last=%s'
              % (sign, ring, len(rs), n_clock, clocks[0], clocks[-1]))

# ---------------------------------------------- 5. TTR resample pool sizes --
print('\n== 5. TTR resample pools ==')
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

targets = [(pg, len(M.bpe_apply(w))) for pg, ws in lab_by_page.items() for w in ws]
pool_sizes, pool_distinct, plan_keys = [], [], []
fallbacks = 0
for pg, L in targets:
    d = by_len.get(pg, {})
    if L in d and d[L]:
        key = (pg, L)
        pool = d[L]
    elif d:
        best = min(d.keys(), key=lambda k: (abs(k - L), k))
        key = (pg, best); pool = d[best]; fallbacks += 1
    else:
        fallbacks += 1
        continue
    plan_keys.append(key)
    pool_sizes.append(len(pool))
    pool_distinct.append(len(set(pool)))
print('  targets %d, exact-length misses %d' % (len(targets), fallbacks))
print('  pool token size: median %d  mean %.1f  min %d  max %d'
      % (statistics.median(pool_sizes), statistics.fmean(pool_sizes),
         min(pool_sizes), max(pool_sizes)))
print('  pool DISTINCT size: median %d  mean %.1f  min %d  max %d'
      % (statistics.median(pool_distinct), statistics.fmean(pool_distinct),
         min(pool_distinct), max(pool_distinct)))
# ceiling: best possible TTR under this resampling design
cnt = Counter(plan_keys)
dist = {}
for pg, ws in txt_by_page.items():
    pass
ceil_types = 0
for key, ntimes in cnt.items():
    pg, L = key
    ceil_types += min(ntimes, len(set(by_len[pg][L])))
print('  CEILING on resample TTR (draw distinct wherever possible): %.4f'
      % (ceil_types / len(plan_keys)))
# label side ceiling for comparison: labels drawn from the same page/length cells
lab_targets = defaultdict(list)
for pg, ws in lab_by_page.items():
    for w in ws:
        lab_targets[(pg, len(M.bpe_apply(w)))].append(w)
lab_ceil = sum(min(len(v), len(set(v))) for v in lab_targets.values()) / sum(len(v) for v in lab_targets.values())
print('  observed label TTR within same cells: %.4f'
      % (sum(len(set(v)) for v in lab_targets.values()) / sum(len(v) for v in lab_targets.values())))
allw = [w for ws in lab_by_page.values() for w in ws]
print('  observed label TTR global: %.4f (%d tokens)' % (len(set(allw)) / len(allw), len(allw)))
